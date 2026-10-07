import datetime
import sqlite3

def erstelle_tabelle():
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patienten (
            id INTEGER PRIMARY KEY,
            name TEXT,
            diagnose TEXT
        )
    """)
    verbindung.commit()
    verbindung.close()

def patient_hinzufuegen(name, diagnose):
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    cursor.execute("INSERT INTO patienten (name, diagnose) VALUES (?, ?)", (name, diagnose))
    verbindung.commit()
    neue_id = cursor.lastrowid
    verbindung.close()
    return neue_id

def erstelle_condition_tabelle():
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conditions (
            id INTEGER PRIMARY KEY,
            patient_id INTEGER,
            code_text TEXT,
            category_text TEXT,
            clinical_status TEXT,
            FOREIGN KEY (patient_id) REFERENCES patienten (id)
        )
    """)
    verbindung.commit()
    verbindung.close()

def condition_hinzufuegen(patient_id, code_text, category_text, clinical_status="active"):
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    cursor.execute(
        "INSERT INTO conditions (patient_id, code_text, category_text, clinical_status) VALUES (?, ?, ?, ?)",
        (patient_id, code_text, category_text, clinical_status)
    )
    verbindung.commit()
    verbindung.close()

def patient_mit_diagnosen_anzeigen():
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    cursor.execute("""
        SELECT patienten.name, conditions.code_text, conditions.category_text, conditions.clinical_status
        FROM patienten
        JOIN conditions ON patienten.id = conditions.patient_id
    """)
    ergebnisse = cursor.fetchall()
    for zeile in ergebnisse:
        print(zeile)
    verbindung.close()

def patient_loeschen(patient_id):
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    cursor.execute("DELETE FROM risk_scores WHERE patient_id = ?", (patient_id,))
    cursor.execute("DELETE FROM conditions WHERE patient_id = ?", (patient_id,))
    cursor.execute("DELETE FROM patienten WHERE id = ?", (patient_id,))
    verbindung.commit()
    verbindung.close()


def erstelle_risk_score_tabelle():
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS risk_scores (
            id INTEGER PRIMARY KEY,
            patient_id INTEGER,
            datum TEXT,
            alter_wert INTEGER,
            cholesterin REAL,
            hdl REAL,
            blutdruck REAL,
            raucher INTEGER,
            behandelt INTEGER,
            risiko_prozent REAL,
            zigaretten_pro_tag INTEGER,
            FOREIGN KEY (patient_id) REFERENCES patienten (id)
        )
    """)
    # Bestehende Datenbanken (ohne die neue Spalte) beim Start erweitern
    spalten = [zeile[1] for zeile in cursor.execute("PRAGMA table_info(risk_scores)")]
    if "zigaretten_pro_tag" not in spalten:
        cursor.execute("ALTER TABLE risk_scores ADD COLUMN zigaretten_pro_tag INTEGER")
    verbindung.commit()
    verbindung.close()

def hole_neuestes_risiko(patient_id):
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    cursor.execute("""
        SELECT risiko_prozent, datum
        FROM risk_scores
        WHERE patient_id = ?
        ORDER BY datum DESC, id DESC
        LIMIT 1
    """, (patient_id,))
    ergebnis = cursor.fetchone()
    verbindung.close()
    return ergebnis

def risiko_speichern(patient_id, alter_wert, cholesterin, hdl, blutdruck, raucher, behandelt, risiko_prozent,
                     zigaretten_pro_tag=None):
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    cursor.execute(
        "INSERT INTO risk_scores (patient_id, datum, alter_wert, cholesterin, hdl, blutdruck, raucher, behandelt, risiko_prozent, zigaretten_pro_tag) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (patient_id, datetime.date.today().isoformat(), alter_wert, cholesterin, hdl, blutdruck, raucher, behandelt, risiko_prozent, zigaretten_pro_tag)
    )
    verbindung.commit()
    verbindung.close()


def hole_alle_risiken(patient_id):
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    cursor.execute("""
        SELECT risiko_prozent, datum
        FROM risk_scores
        WHERE patient_id = ?
        ORDER BY datum DESC, id DESC
    """, (patient_id,))
    ergebnisse = cursor.fetchall()
    verbindung.close()
    return ergebnisse


def erstelle_besuche_tabelle():
    """Zaehlt Besucher ohne personenbezogene Daten: nur ein zufaelliger Token (keine IP-Adresse)."""
    verbindung = sqlite3.connect("patienten.db")
    verbindung.execute("""
        CREATE TABLE IF NOT EXISTS besuche (
            token TEXT PRIMARY KEY,
            erster_besuch TEXT
        )
    """)
    verbindung.commit()
    verbindung.close()


def besuch_zaehlen(token):
    verbindung = sqlite3.connect("patienten.db")
    verbindung.execute("INSERT OR IGNORE INTO besuche (token, erster_besuch) VALUES (?, ?)",
                       (token, datetime.datetime.now().isoformat(timespec="seconds")))
    verbindung.commit()
    verbindung.close()


def hole_statistik():
    """Gesamtzahlen: Besucher, Patienten, Berechnungen, durchschnittliches Risiko."""
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    besucher = cursor.execute("SELECT COUNT(*) FROM besuche").fetchone()[0]
    patienten = cursor.execute("SELECT COUNT(*) FROM patienten").fetchone()[0]
    berechnungen, durchschnitt = cursor.execute(
        "SELECT COUNT(*), AVG(risiko_prozent) FROM risk_scores").fetchone()
    verbindung.close()
    return {"besucher": besucher, "patienten": patienten, "berechnungen": berechnungen,
            "durchschnitt": round(durchschnitt, 1) if durchschnitt is not None else None}


def hole_alle_eintraege(limit=200):
    """Alle Berechnungen (neueste zuerst) inkl. Name - Anonymisierung passiert erst in der App."""
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    cursor.execute("""
        SELECT risk_scores.id, risk_scores.patient_id, risk_scores.datum, risk_scores.alter_wert,
               risk_scores.cholesterin, risk_scores.hdl, risk_scores.blutdruck, risk_scores.raucher,
               risk_scores.zigaretten_pro_tag, risk_scores.risiko_prozent, patienten.name
        FROM risk_scores LEFT JOIN patienten ON patienten.id = risk_scores.patient_id
        ORDER BY risk_scores.datum DESC, risk_scores.id DESC
        LIMIT ?
    """, (limit,))
    ergebnisse = cursor.fetchall()
    verbindung.close()
    return ergebnisse
