from flask import Flask, request, render_template
from fhir_db import (
    patient_hinzufuegen, condition_hinzufuegen, patient_loeschen,
    risiko_speichern, hole_neuestes_risiko
)
from translations import texte, diagnose_uebersetzung
from risk import framingham
import sqlite3

app = Flask(__name__)


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
    sprache = request.args.get("lang", "de")
    t = texte[sprache]
    daten = hole_patienten_mit_diagnosen()

    patienten_gruppiert = {}
    for name, diagnose, kategorie, patient_id in daten:
        if diagnose is None:
            diagnose_angezeigt = "Keine Diagnose"
        elif sprache != "de" and diagnose in diagnose_uebersetzung:
            diagnose_angezeigt = diagnose_uebersetzung[diagnose][sprache]
        else:
            diagnose_angezeigt = diagnose
        if patient_id not in patienten_gruppiert:
            risiko = hole_neuestes_risiko(patient_id)
            patienten_gruppiert[patient_id] = {
                "name": name,
                "diagnosen": [],
                "risiko": risiko
            }
        patienten_gruppiert[patient_id]["diagnosen"].append(diagnose_angezeigt)

    richtung = "rtl" if sprache == "ar" else "ltr"

    return render_template("home.html",
        titel=t['titel'],
        patienten_titel=t['patienten'],
        patienten=patienten_gruppiert,
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


@app.route("/loeschen/<int:patient_id>")
def loeschen(patient_id):
    patient_loeschen(patient_id)

    return render_template("bestaetigung.html",
        titel="MediLink",
        richtung="ltr",
        nachricht="Patient erfolgreich gelöscht."
    )


@app.route("/risiko")
def risiko_formular():
    sprache = request.args.get("lang", "de")
    t = texte[sprache]
    richtung = "rtl" if sprache == "ar" else "ltr"
    return render_template("risiko.html", titel=t['titel'], richtung=richtung, t=t)


@app.route("/risiko_berechnen", methods=["POST"])
def risiko_berechnen():
    name = request.form["name"]
    sex = request.form["sex"]
    alter = int(request.form["alter"])
    cholesterin = float(request.form["cholesterin"])
    hdl = float(request.form["hdl"])
    blutdruck = float(request.form["blutdruck"])
    raucher = "raucher" in request.form
    behandelt = "behandelt" in request.form

    patient_id = patient_hinzufuegen(name, "siehe conditions")
    risiko_prozent = framingham(sex, alter, cholesterin, hdl, blutdruck, behandelt, raucher)
    risiko_speichern(patient_id, alter, cholesterin, hdl, blutdruck, raucher, behandelt, risiko_prozent)

    return render_template("bestaetigung.html",
        titel="MediLink",
        richtung="ltr",
        nachricht=f"Risiko berechnet: {risiko_prozent}% (10-Jahres-Risiko). Dies ist eine Abschätzung, kein Diagnoseinstrument."
    )


if __name__ == "__main__":
    app.run(debug=True)