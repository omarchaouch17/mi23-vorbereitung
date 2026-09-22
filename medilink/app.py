from flask import Flask, request

from fhir_db import patient_mit_diagnosen_anzeigen
import sqlite3

def hole_patienten_mit_diagnosen():
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    cursor.execute("""
        SELECT patienten.name, conditions.code_text, conditions.category_text
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
    for name, diagnose, kategorie in daten:
        if sprache != "de" and diagnose in diagnose_uebersetzung:
            diagnose_angezeigt = diagnose_uebersetzung[diagnose][sprache]
        else:
            diagnose_angezeigt = diagnose
        zeilen_html += f"<p>{name} — {diagnose_angezeigt}</p>"    # ← nicht eingerückt!
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
        {zeilen_html}
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=True)