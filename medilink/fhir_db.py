import datetime

import db


def erstelle_tabelle():
    db.ausfuehren(f"""
        CREATE TABLE IF NOT EXISTS patienten (
            id {db.id_spalte()},
            name TEXT,
            diagnose TEXT
        )
    """)


def patient_hinzufuegen(name, diagnose):
    return db.einfuegen("INSERT INTO patienten (name, diagnose) VALUES (?, ?)", (name, diagnose))


def erstelle_condition_tabelle():
    db.ausfuehren(f"""
        CREATE TABLE IF NOT EXISTS conditions (
            id {db.id_spalte()},
            patient_id INTEGER,
            code_text TEXT,
            category_text TEXT,
            clinical_status TEXT,
            FOREIGN KEY (patient_id) REFERENCES patienten (id)
        )
    """)


def condition_hinzufuegen(patient_id, code_text, category_text, clinical_status="active"):
    db.ausfuehren(
        "INSERT INTO conditions (patient_id, code_text, category_text, clinical_status) VALUES (?, ?, ?, ?)",
        (patient_id, code_text, category_text, clinical_status)
    )


def patient_mit_diagnosen_anzeigen():
    for zeile in db.abfrage("""
        SELECT patienten.name, conditions.code_text, conditions.category_text, conditions.clinical_status
        FROM patienten
        JOIN conditions ON patienten.id = conditions.patient_id
    """):
        print(zeile)


def patient_loeschen(patient_id):
    db.mehrere([
        ("DELETE FROM risk_scores WHERE patient_id = ?", (patient_id,)),
        ("DELETE FROM conditions WHERE patient_id = ?", (patient_id,)),
        ("DELETE FROM patienten WHERE id = ?", (patient_id,)),
    ])


def erstelle_risk_score_tabelle():
    db.ausfuehren(f"""
        CREATE TABLE IF NOT EXISTS risk_scores (
            id {db.id_spalte()},
            patient_id INTEGER,
            datum TEXT,
            alter_wert INTEGER,
            cholesterin DOUBLE PRECISION,
            hdl DOUBLE PRECISION,
            blutdruck DOUBLE PRECISION,
            raucher INTEGER,
            behandelt INTEGER,
            risiko_prozent DOUBLE PRECISION,
            zigaretten_pro_tag INTEGER,
            FOREIGN KEY (patient_id) REFERENCES patienten (id)
        )
    """)
    # Bestehende Datenbanken (ohne die neue Spalte) beim Start erweitern
    if "zigaretten_pro_tag" not in db.spalten("risk_scores"):
        db.ausfuehren("ALTER TABLE risk_scores ADD COLUMN zigaretten_pro_tag INTEGER")


def hole_neuestes_risiko(patient_id):
    zeilen = db.abfrage("""
        SELECT risiko_prozent, datum
        FROM risk_scores
        WHERE patient_id = ?
        ORDER BY datum DESC, id DESC
        LIMIT 1
    """, (patient_id,))
    return zeilen[0] if zeilen else None


def risiko_speichern(patient_id, alter_wert, cholesterin, hdl, blutdruck, raucher, behandelt, risiko_prozent,
                     zigaretten_pro_tag=None):
    db.ausfuehren(
        "INSERT INTO risk_scores (patient_id, datum, alter_wert, cholesterin, hdl, blutdruck, raucher, behandelt, risiko_prozent, zigaretten_pro_tag) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (patient_id, datetime.date.today().isoformat(), alter_wert, cholesterin, hdl, blutdruck,
         int(bool(raucher)), int(bool(behandelt)), risiko_prozent, zigaretten_pro_tag)
    )


def hole_alle_risiken(patient_id):
    return db.abfrage("""
        SELECT risiko_prozent, datum
        FROM risk_scores
        WHERE patient_id = ?
        ORDER BY datum DESC, id DESC
    """, (patient_id,))


def hole_patienten_mit_diagnosen():
    """(name, diagnose, kategorie, patient_id) - Patienten ohne Diagnose haben None."""
    return db.abfrage("""
        SELECT patienten.name, conditions.code_text, conditions.category_text, patienten.id
        FROM patienten
        LEFT JOIN conditions ON patienten.id = conditions.patient_id
        ORDER BY patienten.id, conditions.id
    """)


def hole_alle_patienten():
    """Alle Patienten als [(id, name), ...], alphabetisch."""
    return db.abfrage("SELECT id, name FROM patienten ORDER BY LOWER(name), id")


def erstelle_besuche_tabelle():
    """Zaehlt Besucher ohne personenbezogene Daten: nur ein zufaelliger Token (keine IP-Adresse)."""
    db.ausfuehren("""
        CREATE TABLE IF NOT EXISTS besuche (
            token TEXT PRIMARY KEY,
            erster_besuch TEXT
        )
    """)


def besuch_zaehlen(token):
    db.ausfuehren(
        "INSERT INTO besuche (token, erster_besuch) VALUES (?, ?) ON CONFLICT (token) DO NOTHING",
        (token, datetime.datetime.now().isoformat(timespec="seconds")))


def hole_statistik():
    """Gesamtzahlen: Besucher, Patienten, Berechnungen, durchschnittliches Risiko."""
    besucher = db.abfrage("SELECT COUNT(*) FROM besuche")[0][0]
    patienten = db.abfrage("SELECT COUNT(*) FROM patienten")[0][0]
    berechnungen, durchschnitt = db.abfrage("SELECT COUNT(*), AVG(risiko_prozent) FROM risk_scores")[0]
    return {"besucher": besucher, "patienten": patienten, "berechnungen": berechnungen,
            "durchschnitt": round(float(durchschnitt), 1) if durchschnitt is not None else None}


def hole_alle_eintraege(limit=200):
    """Alle Berechnungen (neueste zuerst) inkl. Name - Anonymisierung passiert erst in der App."""
    return db.abfrage("""
        SELECT risk_scores.id, risk_scores.patient_id, risk_scores.datum, risk_scores.alter_wert,
               risk_scores.cholesterin, risk_scores.hdl, risk_scores.blutdruck, risk_scores.raucher,
               risk_scores.zigaretten_pro_tag, risk_scores.risiko_prozent, patienten.name
        FROM risk_scores LEFT JOIN patienten ON patienten.id = risk_scores.patient_id
        ORDER BY risk_scores.datum DESC, risk_scores.id DESC
        LIMIT ?
    """, (limit,))
