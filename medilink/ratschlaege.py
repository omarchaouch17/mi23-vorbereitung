"""ratschlaege.py - allgemeine Hinweise zum Framingham-Ergebnis (regelbasiert, transparent).

Keine Diagnose, keine Medikamente, keine Dosierungen - nur allgemeine Informationen.
Die Texte stehen in translations.py (Schluessel tipp_*, kat_*, notfall).
"""

# Kategorien nach ATP III (10-Jahres-Risiko, "hard CHD"): unter 10 % niedrig, 10-20 % mittel, ueber 20 % hoch
GRENZE_MITTEL = 10.0
GRENZE_HOCH = 20.0

# Einzelne Werte, die einen zusaetzlichen Hinweis ausloesen (ATP III / Blutdruck-Grenze 140 mmHg)
CHOLESTERIN_HOCH = 240   # mg/dL
HDL_NIEDRIG = {"m": 40, "f": 50}   # mg/dL
BLUTDRUCK_ERHOEHT = 140  # mmHg


def risiko_kategorie(prozent):
    """'niedrig' (<10 %), 'mittel' (10-20 %) oder 'hoch' (>20 %)."""
    if prozent > GRENZE_HOCH:
        return "hoch"
    if prozent >= GRENZE_MITTEL:
        return "mittel"
    return "niedrig"


def hole_tipps(werte, kategorie):
    """Liste von Text-Schluesseln (in dieser Reihenfolge anzeigen).

    werte: bereinigte Eingaben aus validiere_risiko (sex, cholesterin, hdl, blutdruck, raucher).
    """
    tipps = ["tipp_" + kategorie]          # Arztempfehlung passend zur Kategorie
    if werte["raucher"]:
        tipps.append("tipp_rauchen")
    if werte["blutdruck"] >= BLUTDRUCK_ERHOEHT:
        tipps.append("tipp_blutdruck")
    if werte["cholesterin"] >= CHOLESTERIN_HOCH:
        tipps.append("tipp_cholesterin")
    if werte["hdl"] < HDL_NIEDRIG[werte["sex"]]:
        tipps.append("tipp_hdl")
    tipps += ["tipp_bewegung", "tipp_ernaehrung"]
    return tipps
