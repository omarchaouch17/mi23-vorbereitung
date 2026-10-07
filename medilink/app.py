import sqlite3

from flask import Flask, request, render_template, redirect

from fhir_db import (
    erstelle_tabelle, erstelle_condition_tabelle, erstelle_risk_score_tabelle,
    patient_hinzufuegen, condition_hinzufuegen, patient_loeschen,
    risiko_speichern, hole_neuestes_risiko, hole_alle_risiken
)
from translations import texte, diagnose_uebersetzung
from risk import framingham

app = Flask(__name__)

# Tabellen beim Start anlegen (wichtig für Render, dort gibt es keine fertige DB)
erstelle_tabelle()
erstelle_condition_tabelle()
erstelle_risk_score_tabelle()


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
            patienten_gruppiert[patient_id] = {
                "name": name,
                "diagnosen": [],
                "risiko": hole_neuestes_risiko(patient_id)
            }
        patienten_gruppiert[patient_id]["diagnosen"].append(diagnose_angezeigt)

    richtung = "rtl" if sprache == "ar" else "ltr"

    return render_template(
        "home.html",
        titel=t["titel"],
        patienten_titel=t["patienten"],