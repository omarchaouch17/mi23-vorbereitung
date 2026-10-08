"""db.py - eine Datenbank-Schicht fuer zwei Welten:

* ohne DATABASE_URL  -> SQLite-Datei patienten.db (lokal und in den Tests)
* mit  DATABASE_URL  -> PostgreSQL (z. B. Neon). Die Daten bleiben dauerhaft erhalten,
                        auch wenn der Render-Server neu startet oder neu deployed wird.

Alle SQL-Anweisungen werden mit ? geschrieben; fuer PostgreSQL wird das automatisch zu %s.
"""
import os
import sqlite3


def postgres_aktiv():
    return bool(os.environ.get("DATABASE_URL"))


def _pg_url():
    url = os.environ["DATABASE_URL"]
    if url.startswith("postgres://"):          # aeltere Schreibweise
        url = "postgresql://" + url[len("postgres://"):]
    return url


def verbinden():
    if postgres_aktiv():
        import psycopg                           # nur noetig, wenn PostgreSQL benutzt wird
        return psycopg.connect(_pg_url(), connect_timeout=10)
    return sqlite3.connect("patienten.db")


def _sql(sql):
    return sql.replace("?", "%s") if postgres_aktiv() else sql


def id_spalte():
    """Spaltentyp fuer die automatische ID."""
    return "SERIAL PRIMARY KEY" if postgres_aktiv() else "INTEGER PRIMARY KEY"


def abfrage(sql, params=()):
    """SELECT -> Liste von Tupeln."""
    verbindung = verbinden()
    try:
        return verbindung.execute(_sql(sql), params).fetchall()
    finally:
        verbindung.close()


def ausfuehren(sql, params=()):
    """INSERT/UPDATE/DELETE/CREATE ohne Rueckgabe."""
    mehrere([(sql, params)])


def mehrere(anweisungen):
    """Mehrere Anweisungen in EINER Transaktion (alles oder nichts)."""
    verbindung = verbinden()
    try:
        for sql, params in anweisungen:
            verbindung.execute(_sql(sql), params)
        verbindung.commit()
    finally:
        verbindung.close()


def einfuegen(sql, params=()):
    """INSERT und die neue ID zurueckgeben (Tabelle braucht die Spalte id)."""
    verbindung = verbinden()
    try:
        if postgres_aktiv():
            neue_id = verbindung.execute(_sql(sql) + " RETURNING id", params).fetchone()[0]
        else:
            neue_id = verbindung.execute(sql, params).lastrowid
        verbindung.commit()
        return neue_id
    finally:
        verbindung.close()


def spalten(tabelle):
    """Namen der vorhandenen Spalten (fuer einfache Migrationen)."""
    if postgres_aktiv():
        zeilen = abfrage("SELECT column_name FROM information_schema.columns WHERE table_name = ?", (tabelle,))
        return [z[0] for z in zeilen]
    verbindung = verbinden()
    try:
        return [z[1] for z in verbindung.execute(f"PRAGMA table_info({tabelle})")]
    finally:
        verbindung.close()
