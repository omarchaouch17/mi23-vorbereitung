from flask import Flask, request, render_template
from fhir_db import patient_mit_diagnosen_anzeigen, patient_hinzufuegen, condition_hinzufuegen, patient_loeschen, risiko_speichern
from translations import texte, diagnose_uebersetzung # type: ignore
import sqlite3
from risk import framingham
from fhir_db import risiko_speichern, erstelle_risk_score_tabelle


def hole_patienten_mit_diagnosen():
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    cursor.execute("""
        SELECT patienten.name, conditions.code_text, conditions.category_text, patienten.id
        FROM patienten
        JOIN conditions ON patienten.id = conditions.patient_id
    """)
    ergebnisse = cursor.fetchall()
    verbindung.close()
    return ergebnisse

app = Flask(__name__)


@app.route("/")
def home():
    sprache = request.args.get("lang", "de")
    t = texte[sprache]
    daten = hole_patienten_mit_diagnosen()

    patienten_liste = []
    for name, diagnose, kategorie, patient_id in daten:
        if sprache != "de" and diagnose in diagnose_uebersetzung:
            diagnose_angezeigt = diagnose_uebersetzung[diagnose][sprache]
        else:
            diagnose_angezeigt = diagnose
        patienten_liste.append((name, diagnose_angezeigt, patient_id))

    richtung = "rtl" if sprache == "ar" else "ltr"

    return render_template("home.html",
        titel=t['titel'],
        patienten_titel=t['patienten'],
        patienten=patienten_liste,
        richtung=richtung
    )


@app.route("/neu")
def neues_formular():
    return render_template("neu.html", titel="MediLink", richtung="ltr")


@app.route("/hinzufuegen", methods=["POST"])
def hinzufuegen():
    name = request.form["name"]
    diagnose = request.form["diagnose"]
    kategorie = request.form["kategorie"]

    patient_id = patient_hinzufuegen(name, "siehe conditions")
    condition_hinzufuegen(patient_id, diagnose, kategorie)

    return render_template("bestaetigung.html",
        titel="MediLink",
        richtung="ltr",
        nachricht="Patient erfolgreich gespeichert."
    )


@app.route("/loeschen/<int:patient_id>", methods=["POST"])
def loeschen(patient_id):
    patient_loeschen(patient_id)

    return render_template("bestaetigung.html",
        titel="MediLink",
        richtung="ltr",
        nachricht="Patient erfolgreich gelöscht."
    )

@app.route("/risiko")
def risiko_formular():
    return render_template("risiko.html", titel="MediLink", richtung="ltr")


@app.route("/risiko_berechnen", methods=["POST"])
def risiko_berechnen():
    patient_id = int(request.form["patient_id"])
    sex = request.form["sex"]
    alter = int(request.form["alter"])
    cholesterin = float(request.form["cholesterin"])
    hdl = float(request.form["hdl"])
    blutdruck = float(request.form["blutdruck"])
    raucher = "raucher" in request.form
    behandelt = "behandelt" in request.form

    risiko_prozent = framingham(sex, alter, cholesterin, hdl, blutdruck, behandelt, raucher)
    risiko_speichern(patient_id, alter, cholesterin, hdl, blutdruck, raucher, behandelt, risiko_prozent)

    return render_template("bestaetigung.html",
        titel="MediLink",
        richtung="ltr",
        nachricht=f"Risiko berechnet: {risiko_prozent}% (10-Jahres-Risiko). Dies ist eine Absch\u00e4tzung, kein Diagnoseinstrument."
    )


if __name__ == "__main__":
    app.run(debug=True)