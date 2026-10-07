import sqlite3

from flask import Flask, request, render_template, redirect, url_for

from fhir_db import (
    erstelle_tabelle, erstelle_condition_tabelle, erstelle_risk_score_tabelle,
    patient_hinzufuegen, condition_hinzufuegen, patient_loeschen,
    risiko_speichern, hole_neuestes_risiko, hole_alle_risiken
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
app.jinja_env.globals.update(kategorie_name=kategorie_name,
                             diagnose_name=uebersetze_diagnose, ANDERE=ANDERE)

# Tabellen beim Start anlegen (wichtig fuer Render, dort gibt es keine fertige DB)
erstelle_tabelle()
erstelle_condition_tabelle()
erstelle_risk_score_tabelle()


def aktuelle_sprache():
    """Sprache aus ?lang=... (GET) oder verstecktem Formularfeld (POST); unbekannt -> Deutsch."""
    sprache = request.values.get("lang", "de")
    return sprache if sprache in texte else "de"


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
            patienten_gruppiert[patient_id] = {
                "name": name,
                "diagnosen": [],
                "risiko": hole_neuestes_risiko(patient_id)
            }
        patienten_gruppiert[patient_id]["diagnosen"].append(diagnose_angezeigt)

    return render_template("home.html", patienten=patienten_gruppiert)


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

    return render_template("bestaetigung.html", nachricht=t["gespeichert"],
                           zeige_sprachen=False)


@app.route("/loeschen/<int:patient_id>", methods=["POST"])
def loeschen(patient_id):
    patient_loeschen(patient_id)
    return redirect(url_for("home", lang=aktuelle_sprache()))


def hole_patienten_liste():
    """Alle Patienten als [(id, name), ...], alphabetisch."""
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    cursor.execute("SELECT id, name FROM patienten ORDER BY name COLLATE NOCASE, id")
    ergebnisse = cursor.fetchall()
    verbindung.close()
    return ergebnisse


def patienten_auswahl():
    """Eintraege fuer die Auswahlliste; bei gleichen Namen wird die ID angehaengt."""
    liste = hole_patienten_liste()
    haeufigkeit = {}
    for _, name in liste:
        haeufigkeit[name] = haeufigkeit.get(name, 0) + 1
    return [(pid, f"{name} (#{pid})" if haeufigkeit[name] > 1 else name) for pid, name in liste]


def _risiko_seite(werte, fehler, status=200):
    """Rendert das Risiko-Formular (leer oder mit Eingaben + roten Meldungen)."""
    return render_template("risiko.html", werte=werte, fehler=fehler, felder=RISIKO_FELDER,
                           patienten=patienten_auswahl(), sprach_pfad="/risiko"), status


@app.route("/risiko")
def risiko_formular():
    # /risiko?patient=3 waehlt den Patienten schon vor
    return _risiko_seite({"patient_id": request.args.get("patient", "")}, {})


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
                     werte["blutdruck"], werte["raucher"], werte["behandelt"], risiko_prozent)

    kategorie = risiko_kategorie(risiko_prozent)
    return render_template("bestaetigung.html",
                           nachricht=f"{werte['name']}: " + t["ergebnis"].format(p=risiko_prozent),
                           kategorie=kategorie, tipps=hole_tipps(werte, kategorie),
                           zeige_sprachen=False)


@app.route("/verlauf/<int:patient_id>")
def verlauf(patient_id):
    return render_template("verlauf.html", risiken=hole_alle_risiken(patient_id),
                           patient_id=patient_id)


if __name__ == "__main__":
    app.run(debug=True)
