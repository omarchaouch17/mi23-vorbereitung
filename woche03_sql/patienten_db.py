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
    verbindung.close()


def alle_patienten_anzeigen():
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    cursor.execute("SELECT * FROM patienten")
    ergebnisse = cursor.fetchall()
    for zeile in ergebnisse:
        print(zeile)
    verbindung.close()

def patient_loeschen(patient_id):
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    # deine Aufgabe: DELETE-Befehl mit ?-Platzhalter
    cursor.execute("DELETE FROM patienten WHERE id = ?", (patient_id,))  
    verbindung.commit()
    verbindung.close()


def diagnose_aktualisieren(patient_id, neue_diagnose):
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    # dein Teil: UPDATE-Befehl mit zwei ?-Platzhaltern
    cursor.execute("UPDATE patienten SET diagnose = ? WHERE id = ?", (neue_diagnose, patient_id))
    verbindung.commit()
    verbindung.close()
