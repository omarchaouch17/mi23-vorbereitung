# MediLink

Mehrsprachige Gesundheits-Webanwendung (Flask + SQLite) mit Framingham-Herzrisiko-Score.
Portfolio-Projekt im Rahmen meines Studiums Medizinische Informatik (HSNR Krefeld).

**Live-Demo:** https://medilink-trbk.onrender.com
(Free-Tier: der erste Aufruf kann ~30 s dauern; die Datenbank wird bei jedem Deploy zurückgesetzt.)

## Ablauf
1. **Neuer Patient** – Name, Diagnose (Auswahlliste oder "Andere"), Kategorie (Auswahlliste).
2. **Automatische Weiterleitung** zur Risikoberechnung, der neue Patient ist bereits ausgewählt.
3. **Risiko-Score** – Geschlecht, Alter, Cholesterin, HDL, Blutdruck, Rauchstatus
   (nie / Ex / aktuell + Zigaretten pro Tag), Blutdruckbehandlung.
4. **Ergebnis** – 10-Jahres-Risiko in %, Risikokategorie (ATP III: <10 / 10–20 / >20 %),
   allgemeine Hinweise, Notruf-Hinweis, Haftungsausschluss.
5. **Verlauf** je Patient; Löschen per POST mit Rückfrage.

## Funktionen
- 4 Sprachen: Deutsch, Englisch, Französisch, Arabisch (inkl. RTL-Layout) – alle Texte, Fehlermeldungen und Hinweise
- Eingabeprüfung auf Server **und** im Browser (rote Fehlermeldungen, Wertebereiche, HDL < Gesamtcholesterin)
- Regelbasierte Hinweise (keine Medikamente/Dosierungen, keine ärztliche Beratung)
- FHIR-inspirierte Datenbank (Patient, Condition, Risk-Score), automatische Migration
- Einstiegsanimation (respektiert `prefers-reduced-motion`)
- ~100 automatisierte Tests (pytest)

## Hinweis zum Rauchen
Der Framingham-Score verwendet nur "aktuell Raucher: ja/nein". Die Zigarettenanzahl wird
zur Dokumentation gespeichert und angezeigt, verändert den Prozentwert aber nicht.

## Lokal starten
```
pip install -r requirements.txt
python app.py        # http://127.0.0.1:5000
python -m pytest -q  # Tests
```

## Struktur
`app.py` (Routen) · `validierung.py` · `risk.py` (Framingham) · `ratschlaege.py` ·
`fhir_db.py` (SQLite) · `translations.py` · `templates/` · `test_app.py`, `test_risk.py`

Kein Diagnoseinstrument – nur zu Lern- und Demonstrationszwecken.
