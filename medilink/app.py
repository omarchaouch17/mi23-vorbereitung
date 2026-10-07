import hmac
import os
import sqlite3
import uuid
from datetime import timedelta

from flask import Flask, request, render_template, redirect, url_for, session, abort

from fhir_db import (
    erstelle_tabelle, erstelle_condition_tabelle, erstelle_risk_score_tabelle,
    patient_hinzufuegen, condition_hinzufuegen, patient_loeschen,
    risiko_speichern, hole_neuestes_risiko, hole_alle_risiken,
    erstelle_besuche_tabelle, besuch_zaehlen, hole_statistik, hole_alle_eintraege
)
from translations import (
    texte, uebersetze_diagnose, kategorie_name, KATEGORIEN, DIAGNOSEN, ANDERE
)
from risk import framingham
from ratschlaege import risiko_kategorie, hole_tipps
from validierung import (
    RISIKO_FELDER, validiere_risiko, validiere_patient
)

app = Flask(__name__)
# Auf Render als Umgebungsvariablen setzen (SECRET_KEY, ADMIN_KEY). Ohne ADMIN_KEY gibt es keinen Admin-Zugang.
app.secret_key = os.environ.get("SECRET_KEY", "medilink-nur-fuer-lokale-tests")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  PERMANENT_SESSION_LIFETIME=timedelta(days=365))
app.jinja_env.globals.update(kategorie_name=kategorie_name,
                             diagnose_name=uebersetze_diagnose, ANDERE=ANDERE)

# Tabellen beim Start anlegen (wichtig fuer Render, dort gibt es keine fertige DB)
erstelle_tabelle()
erstelle_condition_tabelle()
erstelle_risk_score_tabelle()
erstelle_besuche_tabelle()


def aktuelle_sprache():
    """Sprache aus ?lang=... (GET) oder verstecktem Formularfeld (POST); unbekannt -> Deutsch."""
    sprache = request.values.get("lang", "de")
    return sprache if sprache in texte else "de"


def ist_admin():
    return bool(session.get("admin"))


def eigene_ids():
    return set(session.get("eigene", []))


def darf_sehen(patient_id):
    """Eigene Patienten (in diesem Browser angelegt) und Admin duerfen Namen/Verlauf sehen."""
    return ist_admin() or patient_id in eigene_ids()


def merke_patient(patient_id):
    eigene = session.get("eigene", [])
    eigene.append(patient_id)
    session["eigene"] = eigene[-200:]
    session.permanent = True


@app.before_request
def besucher_zaehlen():
    """Jeder Browser wird einmal gezaehlt - nur ueber einen Zufalls-Token, ohne IP-Adresse."""
    if request.method == "GET" and request.endpoint not in (None, "static") and "besucher" not in session:
        session["besucher"] = uuid.uuid4().hex
        session.permanent = True
        besuch_zaehlen(session["besucher"])


@app.context_processor
def sprache_fuer_alle_templates():
    """t, lang, richtung und titel stehen automatisch in JEDEM Template."""
    sprache = aktuelle_sprache()
    return {
        "t": texte[sprache],
        "lang": sprache,
        "richtung": "rtl" if sprache == "ar" else "ltr",
        "titel": texte[sprache]["titel"],
        "sprachen": ["de", "en", "fr", "ar"],
        "sprach_pfad": request.path,
        "zeige_sprachen": True,
    }


def hole_patienten_mit_diagnosen():
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    cursor.execute("""
        SELECT patienten.name, conditions.code_text, conditions.category_text, patienten.id
        FROM patienten
        LEFT JOIN conditions ON patienten.id = conditions.patient_id
    """)
    ergebnisse = cursor.fetchall()
    verbindung.close()
    return ergebnisse


@app.route("/")
def home():
    sprache = aktuelle_sprache()
    t = texte[sprache]

    patienten_gruppiert = {}
    for name, diagnose, kategorie, patient_id in hole_patienten_mit_diagnosen():
        if diagnose is None:
            diagnose_angezeigt = t["keine_diagnose"]
        else:
            diagnose_angezeigt = uebersetze_diagnose(diagnose, sprache)

        if patient_id not in patienten_gruppiert:
            darf = darf_sehen(patient_id)
            patienten_gruppiert[patient_id] = {
                "name": name if darf else f"{t['anonym']} #{patient_id}",
                "darf": darf,
                "diagnosen": [],
                "risiko": hole_neuestes_risiko(patient_id)
            }
        patienten_gruppiert[patient_id]["diagnosen"].append(diagnose_angezeigt)

    return render_template("home.html", patienten=patienten_gruppiert,
                           fremde=any(not p["darf"] for p in patienten_gruppiert.values()))


@app.route("/neu")
def neues_formular():
    return render_template("neu.html", werte={}, fehler={}, kategorien=KATEGORIEN,
                           diagnosen=DIAGNOSEN)


@app.route("/hinzufuegen", methods=["POST"])
def hinzufuegen():
    t = texte[aktuelle_sprache()]
    werte, fehler = validiere_patient(request.form, t)
    if fehler:
        return render_template("neu.html", werte=werte, fehler=fehler,
                               kategorien=KATEGORIEN, diagnosen=DIAGNOSEN,
                               sprach_pfad="/neu"), 400

    patient_id = patient_hinzufuegen(werte["name"], "siehe conditions")
    condition_hinzufuegen(patient_id, werte["diagnose"], werte["kategorie"])

    merke_patient(patient_id)
    # Direkt weiter zur Score-Berechnung, der neue Patient ist schon ausgewaehlt
    return redirect(url_for("risiko_formular", patient=patient_id, neu=1, lang=aktuelle_sprache()))


@app.route("/loeschen/<int:patient_id>", methods=["POST"])
def loeschen(patient_id):
    if not darf_sehen(patient_id):
        abort(403)
    patient_loeschen(patient_id)
    return redirect(url_for("home", lang=aktuelle_sprache()))


def hole_alle_patienten():
    """Alle Patienten als [(id, name), ...], alphabetisch."""
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    cursor.execute("SELECT id, name FROM patienten ORDER BY name COLLATE NOCASE, id")
    ergebnisse = cursor.fetchall()
    verbindung.close()
    return ergebnisse


def hole_patienten_liste():
    """Nur Patienten, die dieser Besucher sehen darf (eigene oder alle fuer Admin)."""
    return [(pid, name) for pid, name in hole_alle_patienten() if darf_sehen(pid)]


def patienten_auswahl():
    """Eintraege fuer die Auswahlliste; bei gleichen Namen wird die ID angehaengt."""
    liste = hole_patienten_liste()
    haeufigkeit = {}
    for _, name in liste:
        haeufigkeit[name] = haeufigkeit.get(name, 0) + 1
    return [(pid, f"{name} (#{pid})" if haeufigkeit[name] > 1 else name) for pid, name in liste]


def rauchzeile(werte, t):
    """z.B. 'Rauchstatus: Raucher, 15 Zigaretten pro Tag' fuer die Ergebnis-Seite."""
    zeile = f"{t['rauchen']}: {t['rauchen_' + werte['rauchen']]}"
    if werte["zigaretten"]:
        zeile += f", {werte['zigaretten']} {t['zigaretten_kurz']}"
    return zeile


def _risiko_seite(werte, fehler, status=200, neu=False):
    """Rendert das Risiko-Formular (leer oder mit Eingaben + roten Meldungen)."""
    return render_template("risiko.html", werte=werte, fehler=fehler, felder=RISIKO_FELDER,
                           patienten=patienten_auswahl(), neu_gespeichert=neu,
                           sprach_pfad="/risiko"), status


@app.route("/risiko")
def risiko_formular():
    # /risiko?patient=3 waehlt den Patienten schon vor
    return _risiko_seite({"patient_id": request.args.get("patient", "")}, {},
                         neu=bool(request.args.get("neu")))


@app.route("/risiko_berechnen", methods=["POST"])
def risiko_berechnen():
    t = texte[aktuelle_sprache()]
    werte, fehler = validiere_risiko(request.form, t, hole_patienten_liste())
    if fehler:
        return _risiko_seite(request.form, fehler, 400)

    try:
        risiko_prozent = framingham(
            werte["sex"], werte["alter"], werte["cholesterin"], werte["hdl"],
            werte["blutdruck"], werte["behandelt"], werte["raucher"]
        )
    except ValueError as e:  # Sicherheitsnetz, falls risk.py strenger wird als validierung.py
        return _risiko_seite(request.form, {"allgemein": str(e)}, 400)

    # Der Score gehoert zum gewaehlten, bereits vorhandenen Patienten (kein neuer Patient mehr)
    risiko_speichern(werte["patient_id"], werte["alter"], werte["cholesterin"], werte["hdl"],
                     werte["blutdruck"], werte["raucher"], werte["behandelt"], risiko_prozent,
                     zigaretten_pro_tag=werte["zigaretten"])

    kategorie = risiko_kategorie(risiko_prozent)
    return render_template("bestaetigung.html",
                           nachricht=f"{werte['name']}: " + t["ergebnis"].format(p=risiko_prozent),
                           rauchzeile=rauchzeile(werte, t),
                           kategorie=kategorie, tipps=hole_tipps(werte, kategorie),
                           zeige_sprachen=False)


@app.route("/verlauf/<int:patient_id>")
def verlauf(patient_id):
    if not darf_sehen(patient_id):
        abort(404)
    return render_template("verlauf.html", risiken=hole_alle_risiken(patient_id),
                           patient_id=patient_id)


@app.route("/admin")
def admin():
    """/admin?key=... schaltet die Admin-Ansicht fuer diesen Browser frei (Schluessel = ADMIN_KEY)."""
    erwartet = os.environ.get("ADMIN_KEY", "")
    if not erwartet or not hmac.compare_digest(request.args.get("key", ""), erwartet):
        abort(404)
    session["admin"] = True
    session.permanent = True
    return redirect(url_for("statistik", lang=aktuelle_sprache()))


@app.route("/statistik")
def statistik():
    admin_modus = ist_admin()
    eigene = eigene_ids()
    eintraege = []
    for (eid, pid, datum, alter, chol, hdl, bp, raucher, zig, prozent, name) in hole_alle_eintraege():
        eintrag = {"nr": eid, "datum": datum, "alter": alter, "prozent": prozent,
                   "kategorie": risiko_kategorie(prozent), "eigener": pid in eigene}
        if admin_modus:   # nur der Admin sieht Namen und Details
            eintrag.update(name=name, chol=chol, hdl=hdl, bp=bp, raucher=raucher, zig=zig)
        eintraege.append(eintrag)
    return render_template("statistik.html", stat=hole_statistik(), eintraege=eintraege,
                           admin=admin_modus)


if __name__ == "__main__":
    app.run(debug=True)
