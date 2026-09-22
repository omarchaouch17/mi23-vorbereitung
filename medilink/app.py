from flask import Flask, request

from fhir_db import patient_mit_diagnosen_anzeigen

from fhir_db import patient_hinzufuegen, condition_hinzufuegen

from fhir_db import patient_loeschen



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

diagnose_uebersetzung = {
    "Herzinsuffizienz": {"en": "Heart failure", "fr": "Insuffisance cardiaque", "ar": "قصور القلب"},
    "Appendizitis": {"en": "Appendicitis", "fr": "Appendicite", "ar": "التهاب الزائدة الدودية"},
    "Kolonkarzinom": {"en": "Colon cancer", "fr": "Cancer du côlon", "ar": "سرطان القولون"}
}

texte = {
    "de": {"titel": "MediLink", "patienten": "Patienten", "diagnose": "Diagnose"},
    "en": {"titel": "MediConnect", "patienten": "Patients", "diagnose": "Diagnosis"},
    "fr": {"titel": "MédiLien", "patienten": "Patients", "diagnose": "Diagnostic"},
    "ar": {"titel": "رابط طبي", "patienten": "المرضى", "diagnose": "التشخيص"}
}



@app.route("/")
def home():
    sprache = request.args.get("lang", "de")  # default: Deutsch
    t = texte[sprache]
    daten = hole_patienten_mit_diagnosen()
    zeilen_html = ""
    for name, diagnose, kategorie, patient_id in daten:
        if sprache != "de" and diagnose in diagnose_uebersetzung:
            diagnose_angezeigt = diagnose_uebersetzung[diagnose][sprache]
        else:
            diagnose_angezeigt = diagnose
        zeilen_html += f"<p>{name} — {diagnose_angezeigt} <a href='/loeschen/{patient_id}' style='color:#f87171;'>[löschen]</a></p>"    # ← nicht eingerückt!
    richtung = "rtl" if sprache == "ar" else "ltr"

    return f"""
    <html dir="{richtung}">
    <head>
        <title>{t['titel']}</title>
        <style>
            body {{
                background-color: #0f172a;
                color: #e2e8f0;
                font-family: 'Segoe UI', sans-serif;
                text-align: center;
                padding-top: 80px;
            }}
            h1 {{ color: #38bdf8; }}
            .lang-switch a {{
                color: #94a3b8;
                margin: 0 10px;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="lang-switch">
            <a href="/?lang=de">DE</a> | <a href="/?lang=en">EN</a> | <a href="/?lang=fr">FR</a> | <a href="/?lang=ar">AR</a>
        </div>
        <h1>{t['titel']}</h1>
        <h2>{t['patienten']}</h2>
        <p><a href="/neu" style="color: #38bdf8;">+ Neuen Patienten hinzufügen</a></p>
        {zeilen_html}
    </body>
    </html>
    """

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