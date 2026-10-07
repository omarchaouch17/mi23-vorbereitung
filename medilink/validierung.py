"""validierung.py - Eingabepruefung fuer die Formulare (Server-Seite, massgeblich).

Die Grenzen kommen aus risk.py, damit Formular, Pruefung und Rechnung nie auseinanderlaufen.
"""
import math

from risk import RANGES
from translations import KATEGORIEN, DIAGNOSEN, ANDERE

AGE_RANGE = (30, 79)  # wie in risk.framingham(): Score nur fuer 30-79 Jahre validiert

# Feld -> (Label-Schluessel in translations, Grenzen, nur ganze Zahlen?, Einheit)
RISIKO_FELDER = {
    "alter": ("alter", AGE_RANGE, True, ""),
    "cholesterin": ("cholesterin", RANGES["total_chol"], False, "mg/dL"),
    "hdl": ("hdl", RANGES["hdl"], False, "mg/dL"),
    "blutdruck": ("blutdruck", RANGES["sbp"], False, "mmHg"),
}


def _zahl(text):
    """Text -> float oder None (leer, Buchstaben, nan, inf)."""
    try:
        wert = float(text.strip().replace(",", "."))
    except (ValueError, AttributeError):
        return None
    return wert if math.isfinite(wert) else None


def validiere_risiko(form, t):
    """Prueft das Risiko-Formular. Gibt (werte, fehler) zurueck.

    werte  - bereinigte Eingaben (nur wenn fehler leer ist verwendbar)
    fehler - {feldname: Meldung in der Sprache von t}
    """
    fehler, werte = {}, {}

    name = form.get("name", "").strip()
    if not name:
        fehler["name"] = t["err_required"].format(label=t["name"])
    elif len(name) > 60:
        fehler["name"] = t["err_long"].format(label=t["name"], max=60)
    werte["name"] = name

    sex = form.get("sex", "")
    if sex not in ("m", "f"):
        fehler["sex"] = t["err_sex"]
    werte["sex"] = sex

    for feld, (label_key, (low, high), nur_ganz, _einheit) in RISIKO_FELDER.items():
        label = t[label_key]
        roh = form.get(feld, "")
        if not roh.strip():
            fehler[feld] = t["err_required"].format(label=label)
            continue
        wert = _zahl(roh)
        if wert is None or (nur_ganz and not wert.is_integer()):
            fehler[feld] = t["err_number"].format(label=label)
            continue
        if not low <= wert <= high:
            fehler[feld] = t["err_range"].format(label=label, low=low, high=high)
            continue
        werte[feld] = int(wert) if nur_ganz else wert

    # Logik-Pruefung: HDL ist nur ein Teil des Gesamtcholesterins, also muss es kleiner sein
    if "hdl" in werte and "cholesterin" in werte and werte["hdl"] >= werte["cholesterin"]:
        fehler["hdl"] = t["err_hdl"]

    werte["raucher"] = "raucher" in form
    werte["behandelt"] = "behandelt" in form
    return werte, fehler


def validiere_patient(form, t):
    """Prueft das Formular 'Neuer Patient'. Gibt (werte, fehler) zurueck.

    werte["diagnose"] ist der endgueltig zu speichernde Text (Auswahl oder freie Eingabe);
    werte["diagnose_wahl"] / werte["diagnose_frei"] dienen nur zum erneuten Anzeigen des Formulars.
    """
    labels = {"name": t["neu_name"], "diagnose": t["neu_diagnose"],
              "frei": t["frei_label"], "kategorie": t["neu_kategorie"]}
    fehler, werte = {}, {}

    name = form.get("name", "").strip()
    if not name:
        fehler["name"] = t["err_required"].format(label=labels["name"])
    elif len(name) > 60:
        fehler["name"] = t["err_long"].format(label=labels["name"], max=60)
    werte["name"] = name

    # Diagnose: feste Auswahl oder "Andere" + freies Textfeld
    wahl = form.get("diagnose", "")
    frei = form.get("diagnose_frei", "").strip()
    werte["diagnose_wahl"], werte["diagnose_frei"], werte["diagnose"] = wahl, frei, ""
    if wahl == ANDERE:
        if not frei:
            fehler["diagnose_frei"] = t["err_required"].format(label=labels["frei"])
        elif len(frei) > 80:
            fehler["diagnose_frei"] = t["err_long"].format(label=labels["frei"], max=80)
        else:
            werte["diagnose"] = frei
    elif wahl in DIAGNOSEN:
        werte["diagnose"] = wahl
    else:
        fehler["diagnose"] = t["err_choose"].format(label=labels["diagnose"])

    # Kategorie: nur Werte aus der Liste sind erlaubt
    kategorie = form.get("kategorie", "")
    if kategorie not in KATEGORIEN:
        fehler["kategorie"] = t["err_choose"].format(label=labels["kategorie"])
    werte["kategorie"] = kategorie
    return werte, fehler
