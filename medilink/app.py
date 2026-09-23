from flask import Flask, request, render_template

from fhir_db import patient_mit_diagnosen_anzeigen

from fhir_db import patient_hinzufuegen, condition_hinzufuegen

from fhir_db import patient_loeschen

from translations import texte, diagnose_uebersetzung


import sqlite3



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
    return """
    <html>
    <head>
        <style>
            body { background-color: #0f172a; color: #e2e8f0; font-family: 'Segoe UI', sans-serif; text-align: center; padding-top: 80px; }
            input { padding: 8px; margin: 5px; border-radius: 4px; border: none; }
            button { padding: 8px 20px; background-color: #38bdf8; border: none; border-radius: 4px; cursor: pointer; }
        </style>
    </head>
    <body>
        <h1>Neuer Patient</h1>
        <form action="/hinzufuegen" method="POST">
            <input type="text" name="name" placeholder="Patientenname" required><br>
            <input type="text" name="diagnose" placeholder="Diagnose" required><br>
            <input type="text" name="kategorie" placeholder="Kategorie" required><br>
            <button type="submit">Speichern</button>
        </form>
        <br>
        <a href="/" style="color: #94a3b8;">Zurück zur Übersicht</a>
    </body>
    </html>
    """

@app.route("/hinzufuegen", methods=["POST"])
def hinzufuegen():
    name = request.form["name"]
    diagnose = request.form["diagnose"]
    kategorie = request.form["kategorie"]

    patient_id = patient_hinzufuegen(name, "siehe conditions")
    condition_hinzufuegen(patient_id, diagnose, kategorie)
    return """
    <html>
    <head>
        <meta http-equiv="refresh" content="1;url=/">
    </head>
    <body style="background-color: #0f172a; color: #e2e8f0; font-family: 'Segoe UI', sans-serif; text-align: center; padding-top: 80px;">
        <p>Patient erfolgreich gespeichert.</p>
        <a href="/" style="color: #94a3b8;">Zurück zur Übersicht</a>
    </body>
    </html>
    """

@app.route("/loeschen/<int:patient_id>")
def loeschen(patient_id):
    patient_loeschen(patient_id)
    return f"""
    <html>
    <head><meta http-equiv="refresh" content="1;url=/"></head>
    <body style="background-color: #0f172a; color: #e2e8f0; font-family: 'Segoe UI', sans-serif; text-align: center; padding-top: 80px;">
        <p>Patient deleted.</p>
        <a href="/" style="color: #94a3b8;">Back to overview</a>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=True)