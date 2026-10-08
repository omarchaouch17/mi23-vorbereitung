"""Tests for the MediLink Flask app. Run with: py -m pytest -v"""
import re

import pytest
import app as app_module
from app import app
from translations import texte, diagnose_uebersetzung, kategorie_uebersetzung, KATEGORIEN, DIAGNOSEN, ANDERE

VALID = {"patient_id": "1", "sex": "m", "alter": "55", "cholesterin": "220",
         "hdl": "50", "blutdruck": "140", "rauchen": "nie", "lang": "de"}


@pytest.fixture
def client():
    """A fake browser that sends requests to the app without starting a server."""
    app.config["TESTING"] = True
    c = app.test_client()
    with c.session_transaction() as sitzung:   # Standard-Testbesucher ist Admin (sieht alles)
        sitzung["admin"] = True
        sitzung["besucher"] = "test"
    return c


@pytest.fixture
def besucher():
    """Normaler, fremder Besucher ohne Admin-Rechte."""
    app.config["TESTING"] = True
    c = app.test_client()
    with c.session_transaction() as sitzung:
        sitzung["besucher"] = "fremd"
    return c


@pytest.fixture
def fake_db(monkeypatch):
    """Replace the database functions so tests never touch the real patienten.db."""
    saved = []
    monkeypatch.setattr(app_module, "patient_hinzufuegen",
                        lambda name, text: saved.append(name) or 99)
    monkeypatch.setattr(app_module, "condition_hinzufuegen",
                        lambda patient_id, diagnose, kategorie: None)
    monkeypatch.setattr(app_module, "risiko_speichern", lambda *args, **kwargs: None)
    return saved


_echte_liste = app_module.hole_patienten_liste


@pytest.fixture(autouse=True)
def fake_besuche(monkeypatch):
    """Besucher-Zaehler schreibt nie in die echte Datenbank."""
    gezaehlt = []
    monkeypatch.setattr(app_module, "besuch_zaehlen", gezaehlt.append)
    return gezaehlt


@pytest.fixture(autouse=True)
def fake_patienten(monkeypatch):
    """Vorhandene Patienten fuer die Auswahlliste im Risiko-Formular (nie die echte Datenbank)."""
    monkeypatch.setattr(app_module, "hole_patienten_liste", lambda: [(2, "Anna"), (1, "Demo")])


@pytest.fixture
def fake_risk(monkeypatch):
    """Merkt sich, zu welchen Patienten ein Score gespeichert wird."""
    class Liste(list):
        details = []
    gespeichert = Liste()
    gespeichert.details = []

    def speichern(patient_id, *args, **kwargs):
        gespeichert.append(patient_id)
        gespeichert.details.append((args, kwargs))
    monkeypatch.setattr(app_module, "risiko_speichern", speichern)
    return gespeichert


@pytest.fixture
def fake_home(monkeypatch):
    """Fixed patient list for the start page (no real database access)."""
    monkeypatch.setattr(app_module, "hole_patienten_mit_diagnosen",
                        lambda: [("Anna", "Hypertonie", "Kardiologie", 1), ("Ben", None, None, 2)])
    monkeypatch.setattr(app_module, "hole_neuestes_risiko",
                        lambda pid: (8.3, "2026-10-07") if pid == 1 else None)


@pytest.fixture
def fake_delete(monkeypatch):
    """Replace patient_loeschen so tests never delete real patients."""
    deleted = []
    monkeypatch.setattr(app_module, "patient_loeschen",
                        lambda patient_id: deleted.append(patient_id))
    return deleted


# ---------- bestehende Funktionen ----------

def test_form_page_loads(client):
    assert client.get("/neu").status_code == 200


def test_add_patient_shows_confirmation(client, fake_db):
    response = client.post("/hinzufuegen", data={
        "name": "Test Patient", "diagnose": "Hypertonie", "kategorie": "Kardiologie"})
    assert response.status_code == 302
    assert fake_db == ["Test Patient"]
    ort = response.headers["Location"]
    assert "/risiko?" in ort and "patient=99" in ort and "neu=1" in ort and "lang=de" in ort


def test_add_patient_empty_fields_rejected(client, fake_db):
    response = client.post("/hinzufuegen", data={"name": "", "diagnose": "x", "kategorie": "y"})
    assert response.status_code == 400
    assert fake_db == []


def test_delete_via_get_is_not_allowed(client, fake_delete):
    assert client.get("/loeschen/1").status_code == 405
    assert fake_delete == []


def test_delete_via_post_redirects_and_keeps_language(client, fake_delete):
    response = client.post("/loeschen/1", data={"lang": "fr"})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/?lang=fr")
    assert fake_delete == [1]


# ---------- Sprache: ALLES wechselt ----------

def test_all_languages_have_the_same_keys():
    """Fehlt ein Text in einer Sprache, schlaegt dieser Test fehl (statt KeyError im Browser)."""
    for sprache in ("en", "fr", "ar"):
        assert set(texte[sprache]) == set(texte["de"]), sprache
    for eintrag in diagnose_uebersetzung.values():
        assert set(eintrag) == {"en", "fr", "ar"}


@pytest.mark.parametrize("lang,patienten,keine,risiko_link", [
    ("de", "Patienten", "Keine Diagnose", "Herzrisiko berechnen"),
    ("en", "Patients", "No diagnosis", "Calculate heart risk"),
    ("fr", "Patients", "Aucun diagnostic", "Calculer le risque cardiaque"),
    ("ar", "المرضى", "لا يوجد تشخيص", "حساب خطر القلب"),
])
def test_home_is_fully_translated(client, fake_home, lang, patienten, keine, risiko_link):
    html = client.get(f"/?lang={lang}").get_data(as_text=True)
    assert patienten in html and keine in html and risiko_link in html
    assert f'lang="{lang}"' in html
    # Links behalten die Sprache
    assert f"/risiko?lang={lang}" in html and f"/neu?lang={lang}" in html
    assert f"/verlauf/1?lang={lang}" in html


def test_home_translates_diagnosis_and_has_no_german_leftovers_in_english(client, fake_home):
    html = client.get("/?lang=en").get_data(as_text=True)
    assert "Hypertension" in html
    for deutsch in ("Hypertonie", "löschen", "Verlauf", "Keine Diagnose", "Herzrisiko"):
        assert deutsch not in html


def test_arabic_is_right_to_left(client, fake_home):
    assert 'dir="rtl"' in client.get("/?lang=ar").get_data(as_text=True)
    assert 'dir="ltr"' in client.get("/?lang=en").get_data(as_text=True)


def test_unknown_language_falls_back_to_german(client, fake_home):
    response = client.get("/?lang=xx")
    assert response.status_code == 200
    assert "Patienten" in response.get_data(as_text=True)


@pytest.mark.parametrize("lang,erwartet", [
    ("fr", ["Cholestérol total", "Sexe", "Pression artérielle systolique", "Fumeur", "Plage"]),
    ("en", ["Total cholesterol", "Systolic blood pressure", "Smoker", "Range"]),
    ("ar", ["الكوليسترول الكلي", "ضغط الدم الانقباضي", "مدخّن", "المدى"]),
])
def test_risk_form_labels_follow_language(client, lang, erwartet):
    html = client.get(f"/risiko?lang={lang}").get_data(as_text=True)
    for text in erwartet:
        assert text in html
    for deutsch in ("Gesamtcholesterin", "Raucher", "Zurück", "Blutdruckbehandlung"):
        assert deutsch not in html
    assert f'name="lang" value="{lang}"' in html


def test_risk_form_shows_valid_range_from_the_start(client):
    html = client.get("/risiko").get_data(as_text=True)
    assert "20–100" in html and 'min="20"' in html and 'max="100"' in html   # HDL
    assert "30–79" in html                                                    # Alter
    assert "100–400" in html and "80–220" in html


def test_new_patient_page_translated(client):
    assert "Nouveau patient" in client.get("/neu?lang=fr").get_data(as_text=True)



def test_language_switch_on_risk_page_points_to_get_route(client):
    html = client.get("/risiko?lang=en").get_data(as_text=True)
    assert 'href="/risiko?lang=fr"' in html


# ---------- Eingaben: logisch ab Anfang, rote Meldung sonst ----------

def post_risk(client, **overrides):
    data = dict(VALID, **overrides)
    return client.post("/risiko_berechnen", data=data)


def test_valid_input_saves_once_and_shows_result(client, fake_risk):
    response = post_risk(client)
    assert response.status_code == 200
    assert re.search(r"Risiko berechnet: \d+\.\d%", response.get_data(as_text=True))
    assert fake_risk == [1]   # Score gehoert zum gewaehlten Patienten 1


def test_result_is_in_selected_language(client, fake_risk):
    html = post_risk(client, lang="fr").get_data(as_text=True)
    assert "Risque calculé" in html and "Risiko berechnet" not in html


@pytest.mark.parametrize("feld,wert", [
    ("hdl", "5"), ("hdl", "150"), ("cholesterin", "50"), ("cholesterin", "900"),
    ("blutdruck", "300"), ("blutdruck", "20"), ("alter", "20"), ("alter", "95"),
])
def test_out_of_range_is_rejected_and_nothing_is_saved(client, fake_risk, feld, wert):
    response = post_risk(client, **{feld: wert})
    assert response.status_code == 400
    assert fake_risk == []                      # kein Patient ohne Score
    html = response.get_data(as_text=True)
    assert 'class="fehler"' in html and "muss zwischen" in html
    assert f'value="{wert}"' in html          # Eingabe bleibt erhalten


def test_error_message_is_in_selected_language(client, fake_risk):
    html = post_risk(client, hdl="5", lang="fr").get_data(as_text=True)
    assert "doit être compris entre 20 et 100" in html
    html = post_risk(client, hdl="5", lang="ar").get_data(as_text=True)
    assert "بين 20 و100" in html


def test_empty_and_non_numeric_fields_rejected(client, fake_risk):
    assert post_risk(client, hdl="").status_code == 400
    assert post_risk(client, hdl="abc").status_code == 400
    assert post_risk(client, hdl="nan").status_code == 400
    assert post_risk(client, alter="55.5").status_code == 400
    assert post_risk(client, patient_id="").status_code == 400
    assert post_risk(client, patient_id="999").status_code == 400   # gibt es nicht
    assert post_risk(client, patient_id="abc").status_code == 400
    assert post_risk(client, sex="x").status_code == 400
    assert fake_risk == []


def test_hdl_must_be_lower_than_total_cholesterol(client, fake_risk):
    response = post_risk(client, cholesterin="100", hdl="100")   # beide im Bereich, aber unlogisch
    assert response.status_code == 400
    assert "HDL muss kleiner" in response.get_data(as_text=True)
    assert fake_risk == []


def test_decimal_comma_is_accepted(client, fake_risk):
    assert post_risk(client, cholesterin="220,5").status_code == 200


def test_error_page_language_switch_uses_get_route(client, fake_risk):
    html = post_risk(client, hdl="5").get_data(as_text=True)
    assert 'href="/risiko?lang=en"' in html


# ---------- Kategorie: Auswahl statt Tippen ----------

def test_category_is_a_dropdown_with_all_options(client):
    html = client.get("/neu").get_data(as_text=True)
    assert '<select id="kategorie" name="kategorie"' in html
    assert 'type="text" id="kategorie"' not in html
    for k in KATEGORIEN:
        assert f'value="{k}"' in html


@pytest.mark.parametrize("lang,erwartet", [
    ("en", ["Cardiology", "Internal medicine", "Please select"]),
    ("fr", ["Médecine interne", "Gastro-entérologie", "Veuillez choisir"]),
    ("ar", ["أمراض القلب", "الطب النفسي", "يرجى الاختيار"]),
])
def test_category_options_follow_language(client, lang, erwartet):
    html = client.get(f"/neu?lang={lang}").get_data(as_text=True)
    for text in erwartet:
        assert text in html
    assert "Kardiologie</option>" not in html


def test_every_category_has_all_four_languages():
    for key, namen in kategorie_uebersetzung.items():
        assert set(namen) == {"de", "en", "fr", "ar"}, key


def test_valid_category_is_saved(client, monkeypatch, fake_db):
    gespeichert = []
    monkeypatch.setattr(app_module, "condition_hinzufuegen",
                        lambda pid, diagnose, kategorie: gespeichert.append(kategorie))
    client.post("/hinzufuegen", data={"name": "A", "diagnose": "Asthma", "kategorie": "Pneumologie"})
    assert gespeichert == ["Pneumologie"]


@pytest.mark.parametrize("wert", ["", "Zauberei", "<script>"])
def test_category_outside_list_is_rejected(client, fake_db, wert):
    response = client.post("/hinzufuegen", data={"name": "A", "diagnose": "Asthma", "kategorie": wert})
    assert response.status_code == 400
    assert fake_db == []
    assert "Auswahl" in response.get_data(as_text=True)


def test_selected_category_stays_after_error(client, fake_db):
    html = client.post("/hinzufuegen", data={"name": "", "diagnose": "x",
                                             "kategorie": "Onkologie"}).get_data(as_text=True)
    assert 'value="Onkologie" selected' in html


# ---------- Diagnose: Auswahl + "Andere" ----------

def test_diagnosis_is_a_dropdown_with_other_option(client):
    html = client.get("/neu").get_data(as_text=True)
    assert '<select id="diagnose" name="diagnose"' in html
    for d in DIAGNOSEN:
        assert f'value="{d}"' in html
    assert f'value="{ANDERE}"' in html and 'name="diagnose_frei"' in html


@pytest.mark.parametrize("lang,erwartet", [
    ("en", ["Heart failure", "Stroke", "Other (enter yourself)"]),
    ("fr", ["Insuffisance cardiaque", "Accident vasculaire cérébral (AVC)", "Autre (saisir soi-même)"]),
    ("ar", ["قصور القلب", "السكتة الدماغية", "أخرى (أدخلها بنفسك)"]),
])
def test_diagnosis_options_follow_language(client, lang, erwartet):
    html = client.get(f"/neu?lang={lang}").get_data(as_text=True)
    for text in erwartet:
        assert text in html


def test_all_dropdown_diagnoses_have_translations():
    for d in DIAGNOSEN:
        assert set(diagnose_uebersetzung[d]) == {"en", "fr", "ar"}, d


def post_patient(client, **overrides):
    data = {"name": "A", "diagnose": "Asthma", "kategorie": "Pneumologie"}
    data.update(overrides)
    return client.post("/hinzufuegen", data=data)


def test_listed_diagnosis_is_saved_in_german(client, monkeypatch, fake_db):
    gespeichert = []
    monkeypatch.setattr(app_module, "condition_hinzufuegen",
                        lambda pid, diagnose, kategorie: gespeichert.append(diagnose))
    assert post_patient(client, diagnose="Schlaganfall").status_code == 302
    assert gespeichert == ["Schlaganfall"]


def test_other_diagnosis_uses_free_text(client, monkeypatch, fake_db):
    gespeichert = []
    monkeypatch.setattr(app_module, "condition_hinzufuegen",
                        lambda pid, diagnose, kategorie: gespeichert.append(diagnose))
    response = post_patient(client, diagnose=ANDERE, diagnose_frei="  Gicht ")
    assert response.status_code == 302 and gespeichert == ["Gicht"]


def test_other_without_free_text_is_rejected(client, fake_db):
    response = post_patient(client, diagnose=ANDERE, diagnose_frei="  ")
    assert response.status_code == 400 and fake_db == []
    assert "Pflichtfeld" in response.get_data(as_text=True)


def test_free_text_is_ignored_when_a_listed_diagnosis_is_chosen(client, monkeypatch, fake_db):
    gespeichert = []
    monkeypatch.setattr(app_module, "condition_hinzufuegen",
                        lambda pid, diagnose, kategorie: gespeichert.append(diagnose))
    post_patient(client, diagnose="Asthma", diagnose_frei="irgendwas")
    assert gespeichert == ["Asthma"]


@pytest.mark.parametrize("wert", ["", "Zauberei", "<script>"])
def test_diagnosis_outside_list_is_rejected(client, fake_db, wert):
    response = post_patient(client, diagnose=wert)
    assert response.status_code == 400 and fake_db == []


def test_diagnosis_choice_stays_after_error(client, fake_db):
    html = post_patient(client, name="", diagnose="COPD").get_data(as_text=True)
    assert 'value="COPD" selected' in html


def test_free_diagnosis_is_translated_when_it_matches_the_dictionary(client, fake_home):
    # Eigene Eingabe "hypertonie" (klein geschrieben) wird beim Anzeigen trotzdem uebersetzt
    from translations import uebersetze_diagnose
    assert uebersetze_diagnose("hypertonie", "fr") == "Hypertension artérielle"


# ---------- Risiko-Formular: Patient aus der Liste waehlen ----------

def test_patient_is_a_dropdown_with_existing_names(client):
    html = client.get("/risiko").get_data(as_text=True)
    assert '<select id="patient_id" name="patient_id"' in html
    assert 'name="name"' not in html and 'id="name"' not in html     # kein Tippfeld mehr
    assert ">Anna</option>" in html and ">Demo</option>" in html
    assert html.index(">Anna<") < html.index(">Demo<")


def test_patient_can_be_preselected_by_link(client):
    html = client.get("/risiko?patient=1").get_data(as_text=True)
    assert 'value="1" selected' in html


def test_duplicate_names_get_an_id_suffix(client, monkeypatch):
    monkeypatch.setattr(app_module, "hole_patienten_liste", lambda: [(1, "Omar"), (3, "Omar"), (2, "Anna")])
    html = client.get("/risiko").get_data(as_text=True)
    assert "Omar (#1)" in html and "Omar (#3)" in html and ">Anna</option>" in html


def test_without_patients_the_form_asks_to_add_one_first(client, monkeypatch):
    monkeypatch.setattr(app_module, "hole_patienten_liste", lambda: [])
    html = client.get("/risiko?lang=fr").get_data(as_text=True)
    assert "Aucun patient pour l'instant" in html or "Aucun patient pour l&#39;instant" in html
    assert 'id="risiko-form"' not in html and "/neu?lang=fr" in html


def test_score_is_saved_for_chosen_patient_and_no_new_patient_is_created(client, fake_risk, monkeypatch):
    angelegt = []
    monkeypatch.setattr(app_module, "patient_hinzufuegen", lambda n, d: angelegt.append(n) or 99)
    response = post_risk(client, patient_id="2")
    assert response.status_code == 200 and fake_risk == [2] and angelegt == []
    assert "Anna: Risiko berechnet" in response.get_data(as_text=True)


def test_patient_label_follows_language(client):
    assert "المريض" in client.get("/risiko?lang=ar").get_data(as_text=True)
    assert "Veuillez choisir" in client.get("/risiko?lang=fr").get_data(as_text=True)


# ---------- Mehrere Scores am selben Tag: der zuletzt gespeicherte gilt als neuester ----------

def test_newest_risk_wins_when_two_scores_are_saved_on_the_same_day(tmp_path, monkeypatch):
    import fhir_db
    monkeypatch.chdir(tmp_path)                       # eigene Test-Datenbank, nicht die echte
    fhir_db.erstelle_tabelle(); fhir_db.erstelle_risk_score_tabelle()
    pid = fhir_db.patient_hinzufuegen("Test", "x")
    fhir_db.risiko_speichern(pid, 55, 220, 50, 140, 0, 0, 8.3)
    fhir_db.risiko_speichern(pid, 56, 230, 50, 140, 0, 0, 9.4)
    assert fhir_db.hole_neuestes_risiko(pid)[0] == 9.4
    assert [r[0] for r in fhir_db.hole_alle_risiken(pid)] == [9.4, 8.3]


# ---------- Hinweise zum Ergebnis (regelbasiert) ----------

from ratschlaege import risiko_kategorie, hole_tipps


@pytest.mark.parametrize("prozent,erwartet", [
    (0.0, "niedrig"), (9.9, "niedrig"), (10.0, "mittel"), (20.0, "mittel"), (20.1, "hoch"), (45.0, "hoch"),
])
def test_risk_categories_follow_atp3_thresholds(prozent, erwartet):
    assert risiko_kategorie(prozent) == erwartet


def werte(**o):
    basis = {"sex": "m", "cholesterin": 200.0, "hdl": 55.0, "blutdruck": 120.0, "raucher": False}
    basis.update(o)
    return basis


def test_healthy_values_only_give_basic_tips():
    assert hole_tipps(werte(), "niedrig") == ["tipp_niedrig", "tipp_bewegung", "tipp_ernaehrung"]


def test_each_risk_factor_adds_its_own_tip():
    tipps = hole_tipps(werte(raucher=True, blutdruck=150.0, cholesterin=250.0, hdl=35.0), "hoch")
    assert tipps[0] == "tipp_hoch"
    for k in ("tipp_rauchen", "tipp_blutdruck", "tipp_cholesterin", "tipp_hdl"):
        assert k in tipps


def test_hdl_threshold_differs_by_sex():
    assert "tipp_hdl" not in hole_tipps(werte(sex="m", hdl=45.0), "niedrig")   # Mann: ab 40 ok
    assert "tipp_hdl" in hole_tipps(werte(sex="f", hdl=45.0), "niedrig")       # Frau: unter 50 niedrig


def test_result_page_shows_category_tips_and_emergency_note(client, fake_risk):
    html = post_risk(client, cholesterin="260", blutdruck="150", rauchen="aktuell", zigaretten="15").get_data(as_text=True)
    assert 'class="kat kat-' in html and "Allgemeine Hinweise" in html
    assert "Rauchen" in html and "Blutdruck" in html and "cholesterin" in html
    assert "Notruf 112" in html and "keine ärztliche Beratung" in html


def test_result_page_tips_follow_language(client, fake_risk):
    html = post_risk(client, lang="fr", rauchen="aktuell", zigaretten="15").get_data(as_text=True)
    assert "Conseils généraux" in html and "appelez immédiatement le 112" in html
    assert "Allgemeine Hinweise" not in html
    html = post_risk(client, lang="ar", rauchen="aktuell", zigaretten="15").get_data(as_text=True)
    assert "نصائح عامة" in html and "112" in html


def test_new_patient_lands_on_risk_page_with_banner_and_preselection(client, monkeypatch, fake_db):
    response = post_patient(client, lang="fr")
    assert "lang=fr" in response.headers["Location"]
    monkeypatch.setattr(app_module, "hole_patienten_liste", lambda: [(99, "Neu"), (1, "Demo")])
    html = client.get(response.headers["Location"]).get_data(as_text=True)
    assert "Calculez maintenant le risque cardiaque" in html
    assert re.search(r'<option value="99"\s+selected', html)


def test_risk_page_without_new_flag_has_no_banner(client):
    assert "erfolg-box" not in client.get("/risiko").get_data(as_text=True).split("</style>")[-1]


def test_smoking_select_and_cigarette_box_present(client):
    html = client.get("/risiko").get_data(as_text=True)
    for wert in ("nie", "ex", "aktuell"):
        assert f'value="{wert}"' in html
    assert "Zigaretten pro Tag (Durchschnitt)" in html and 'id="zigaretten-box"' in html


def test_current_smoker_needs_cigarettes(client, fake_risk):
    r = post_risk(client, rauchen="aktuell", zigaretten="")
    assert r.status_code == 400 and fake_risk == []
    for schlecht in ("0", "101", "abc"):
        assert post_risk(client, rauchen="aktuell", zigaretten=schlecht).status_code == 400


def test_smoking_status_required(client, fake_risk):
    data = dict(VALID); del data["rauchen"]
    assert client.post("/risiko_berechnen", data=data).status_code == 400


def test_non_smokers_store_no_cigarettes(client, fake_risk):
    for status in ("nie", "ex"):
        post_risk(client, rauchen=status, zigaretten="30")
    assert [d[1]["zigaretten_pro_tag"] for d in fake_risk.details] == [None, None]


def test_cigarettes_saved_and_shown_on_result(client, fake_risk):
    html = post_risk(client, rauchen="aktuell", zigaretten="15").get_data(as_text=True)
    assert fake_risk.details[0][1]["zigaretten_pro_tag"] == 15
    assert "Rauchstatus: Raucher, 15 Zigaretten pro Tag" in html


def test_smoking_line_follows_language(client, fake_risk):
    html = post_risk(client, lang="en", rauchen="aktuell", zigaretten="5").get_data(as_text=True)
    assert "5 cigarettes per day" in html


def test_db_migration_adds_cigarette_column(tmp_path, monkeypatch):
    import sqlite3, fhir_db
    monkeypatch.chdir(tmp_path)
    con = sqlite3.connect("patienten.db")
    con.execute("CREATE TABLE risk_scores (id INTEGER PRIMARY KEY, patient_id INTEGER, datum TEXT, "
                "alter_jahre INTEGER, total_cholesterin REAL, hdl REAL, blutdruck REAL, "
                "raucher INTEGER, behandelt INTEGER, risiko_prozent REAL)")
    con.commit(); con.close()
    fhir_db.erstelle_risk_score_tabelle()
    con = sqlite3.connect("patienten.db")
    spalten = [r[1] for r in con.execute("PRAGMA table_info(risk_scores)")]
    con.close()
    assert "zigaretten_pro_tag" in spalten


# ---------- Animation beim Betreten ----------

def test_home_has_intro_animation_with_title_in_selected_language(client, fake_home):
    html = client.get("/?lang=fr").get_data(as_text=True)
    assert 'id="intro"' in html and "MédiLien" in html
    assert "prefers-reduced-motion" in html         # respektiert die Systemeinstellung


def test_other_pages_have_no_intro(client, fake_home):
    assert 'id="intro"' not in client.get("/risiko").get_data(as_text=True)
    assert 'id="intro"' not in client.get("/neu").get_data(as_text=True)


# ---------- Anonymitaet, Statistik, Besucherzaehler ----------

@pytest.fixture
def alle_daten(monkeypatch):
    """Zwei fremde Patienten + ein Eintrag; Namen sollen fuer Fremde unsichtbar bleiben."""
    monkeypatch.setattr(app_module, "hole_patienten_mit_diagnosen",
                        lambda: [("Geheim Gerda", "Asthma", "Pneumologie", 7), ("Eigen Egon", "Hypertonie", "Kardiologie", 8)])
    monkeypatch.setattr(app_module, "hole_neuestes_risiko", lambda pid: (8.3, "2026-10-07"))
    monkeypatch.setattr(app_module, "hole_alle_patienten", lambda: [(8, "Eigen Egon"), (7, "Geheim Gerda")])
    monkeypatch.setattr(app_module, "hole_patienten_liste", _echte_liste)
    monkeypatch.setattr(app_module, "hole_statistik",
                        lambda: {"besucher": 12, "patienten": 2, "berechnungen": 1, "durchschnitt": 8.3})
    monkeypatch.setattr(app_module, "hole_alle_eintraege",
                        lambda: [(5, 7, "2026-10-07", 55, 220.0, 50.0, 140.0, 1, 15, 8.3, "Geheim Gerda")])


def test_stranger_sees_other_patients_only_anonymous(besucher, alle_daten):
    html = besucher.get("/").get_data(as_text=True)
    assert "Geheim Gerda" not in html and "Eigen Egon" not in html
    assert "Anonym #7" in html and "Anonym #8" in html
    assert "/verlauf/7" not in html and "/loeschen/7" not in html


def test_visitor_sees_own_patient_by_name(besucher, alle_daten):
    with besucher.session_transaction() as s:
        s["eigene"] = [8]
    html = besucher.get("/").get_data(as_text=True)
    assert "Eigen Egon" in html and "/verlauf/8" in html and "Geheim Gerda" not in html


def test_stranger_cannot_delete_or_open_history_of_others(besucher, alle_daten, fake_delete):
    assert besucher.post("/loeschen/7").status_code == 403 and fake_delete == []
    assert besucher.get("/verlauf/7").status_code == 404


def test_risk_form_lists_only_own_patients_for_strangers(besucher, alle_daten):
    html = besucher.get("/risiko").get_data(as_text=True)
    assert "Geheim Gerda" not in html
    with besucher.session_transaction() as s:
        s["eigene"] = [8]
    assert "Eigen Egon" in besucher.get("/risiko").get_data(as_text=True)


def test_stranger_cannot_calculate_for_foreign_patient(besucher, alle_daten, fake_risk):
    r = besucher.post("/risiko_berechnen", data=dict(VALID, patient_id="7"))
    assert r.status_code == 400 and fake_risk == []


def test_new_patient_becomes_own(besucher, fake_db):
    besucher.post("/hinzufuegen", data={"name": "A", "diagnose": "Asthma", "kategorie": "Pneumologie"})
    with besucher.session_transaction() as s:
        assert s["eigene"] == [99]


def test_statistics_page_is_anonymous_for_strangers(besucher, alle_daten):
    html = besucher.get("/statistik").get_data(as_text=True)
    assert "Geheim Gerda" not in html and "220" not in html and "140" not in html
    assert ">12<" in html and "8.3" in html and "Statistik (anonym)" in html


def test_statistics_page_shows_names_and_values_to_admin(client, alle_daten):
    html = client.get("/statistik").get_data(as_text=True)
    assert "Geheim Gerda" in html and "220" in html and "Admin-Ansicht" in html


def test_statistics_follows_language(besucher, alle_daten):
    assert "Statistiques (anonymes)" in besucher.get("/statistik?lang=fr").get_data(as_text=True)
    assert "الإحصائيات" in besucher.get("/statistik?lang=ar").get_data(as_text=True)


def test_visit_is_counted_once_per_browser(fake_besuche, fake_home):
    c = app.test_client()
    c.get("/"); c.get("/neu"); c.get("/")
    assert len(fake_besuche) == 1


def test_admin_login_needs_correct_key(monkeypatch, alle_daten):
    monkeypatch.setenv("ADMIN_KEY", "geheim123")
    c = app.test_client()
    assert c.get("/admin").status_code == 404
    assert c.get("/admin?key=falsch").status_code == 404
    assert c.get("/admin?key=geheim123").status_code == 302
    assert "Geheim Gerda" in c.get("/statistik").get_data(as_text=True)


def test_admin_disabled_without_env_key(monkeypatch):
    monkeypatch.delenv("ADMIN_KEY", raising=False)
    assert app.test_client().get("/admin?key=").status_code == 404


def test_statistics_db_functions(tmp_path, monkeypatch):
    import fhir_db
    monkeypatch.chdir(tmp_path)
    for f in (fhir_db.erstelle_tabelle, fhir_db.erstelle_condition_tabelle,
              fhir_db.erstelle_risk_score_tabelle, fhir_db.erstelle_besuche_tabelle):
        f()
    fhir_db.besuch_zaehlen("a"); fhir_db.besuch_zaehlen("a"); fhir_db.besuch_zaehlen("b")
    pid = fhir_db.patient_hinzufuegen("X", "y")
    fhir_db.risiko_speichern(pid, 50, 200, 50, 120, 0, 0, 10.0)
    fhir_db.risiko_speichern(pid, 51, 200, 50, 120, 0, 0, 20.0)
    st = fhir_db.hole_statistik()
    assert st == {"besucher": 2, "patienten": 1, "berechnungen": 2, "durchschnitt": 15.0}
    assert len(fhir_db.hole_alle_eintraege()) == 2
    fhir_db.patient_loeschen(pid)
    assert fhir_db.hole_statistik()["berechnungen"] == 0


# ---------- Werte-Erklaerung (Skalen) ----------

def test_risk_page_has_value_guide_with_three_scales(client):
    html = client.get("/risiko").get_data(as_text=True)
    assert html.count('class="skala"') == 3
    for feld in ("cholesterin", "hdl", "blutdruck"):
        assert f'data-feld="{feld}"' in html
    assert "Werte verstehen" in html and "Beispiel" in html


@pytest.mark.parametrize("lang,erwartet", [
    ("en", "Understand the values"), ("fr", "Comprendre les valeurs"), ("ar", "فهم القيم")])
def test_value_guide_follows_language(client, lang, erwartet):
    html = client.get(f"/risiko?lang={lang}").get_data(as_text=True)
    assert erwartet in html and "Werte verstehen" not in html


def test_value_guide_zone_widths_add_up_to_100(client):
    html = client.get("/risiko").get_data(as_text=True)
    breiten = [float(w) for w in re.findall(r'class="zone zone-\w+" style="width: ([\d.]+)%', html)]
    assert len(breiten) == 9
    for i in range(0, 9, 3):
        assert abs(sum(breiten[i:i + 3]) - 100) < 0.1


# ---------- KI-Assistent (Claude API wird immer nur nachgeahmt, nie echt aufgerufen) ----------

import assistent


class _FakeAntwort:
    def __init__(self, text):
        self.content = [type("B", (), {"type": "text", "text": text})()]


@pytest.fixture
def ki(monkeypatch):
    """Aktiviert den Assistenten mit einer gefaelschten API und merkt sich die Aufrufe."""
    aufrufe = []
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(assistent, "_tageszaehler", {})

    class Messages:
        def create(self, **kwargs):
            aufrufe.append(kwargs)
            return _FakeAntwort("HDL ist das gute Cholesterin.")
    monkeypatch.setattr(assistent, "_client", lambda: type("C", (), {"messages": Messages()})())
    return aufrufe


def chat(client, text="Was ist HDL?", lang="de", **extra):
    return client.post(f"/chat?lang={lang}", json=dict({"message": text}, **extra))


def test_without_api_key_the_free_helper_answers(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = chat(client, "Was bedeutet HDL?")
    assert r.status_code == 200 and "gute" in r.get_json()["antwort"]


def test_result_page_always_shows_assistant_box(client, monkeypatch, fake_risk):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    html = client.post("/risiko_berechnen", data=VALID).get_data(as_text=True)
    assert 'id="chat-form"' in html and "Hilfe-Assistent" in html and "keine KI" in html
    assert html.count('class="chip"') == 7 and "Was bedeutet HDL?" in html


def test_chat_box_shown_on_result_page_when_enabled(client, ki, fake_risk):
    html = client.post("/risiko_berechnen", data=VALID).get_data(as_text=True)
    assert 'id="chat-form"' in html and "KI-Assistent" in html and "Anthropic" in html


def test_chat_answers_and_calls_api_with_safety_settings(client, ki):
    r = chat(client)
    assert r.status_code == 200 and r.get_json()["antwort"] == "HDL ist das gute Cholesterin."
    aufruf = ki[0]
    assert aufruf["max_tokens"] <= 400 and "Keine Diagnosen" in aufruf["system"]
    assert aufruf["messages"][-1] == {"role": "user", "content": "Was ist HDL?"}


def test_chat_sends_result_values_but_no_name(client, ki, fake_risk):
    client.post("/risiko_berechnen", data=dict(VALID, cholesterin="233"))
    chat(client)
    system = ki[0]["system"]
    assert "cholesterin=233.0" in system and "Demo" not in system and "Anna" not in system


def test_chat_language_in_system_prompt(client, ki):
    chat(client, lang="fr")
    assert "Français" in ki[0]["system"]


def test_chat_emergency_keywords_skip_ai(client, ki):
    r = chat(client, "Ich habe starke Brustschmerzen")
    assert "112" in r.get_json()["antwort"] and ki == []
    assert "112" in chat(client, "douleur thoracique", lang="fr").get_json()["antwort"]


def test_chat_rejects_empty_and_too_long(client, ki):
    assert chat(client, "   ").status_code == 400
    assert chat(client, "x" * 501).status_code == 400 and ki == []


def test_chat_limit_per_visitor(client, ki):
    for _ in range(assistent.LIMIT_BESUCHER):
        assert chat(client).status_code == 200
    assert chat(client).status_code == 429


def test_chat_daily_limit(client, ki, monkeypatch):
    monkeypatch.setattr(assistent, "TAGESLIMIT", 2)
    assert chat(client).status_code == 200 and chat(client).status_code == 200
    assert chat(client).status_code == 429


def test_chat_api_failure_gives_friendly_error(client, ki, monkeypatch):
    class Kaputt:
        def create(self, **kw):
            raise RuntimeError("boom")
    monkeypatch.setattr(assistent, "_client", lambda: type("C", (), {"messages": Kaputt()})())
    r = chat(client)
    assert r.status_code == 503 and "nicht erreichbar" in r.get_json()["fehler"]


def test_history_is_sanitised():
    sauber = assistent.pruefe_verlauf([
        {"role": "assistant", "content": "alt"}, {"role": "system", "content": "böse"},
        {"role": "user", "content": "hi"}, {"role": "assistant", "content": 5}, "müll"])
    assert sauber == [{"role": "user", "content": "hi"}]


def test_chat_translations_exist_in_all_languages():
    for lang in ("de", "en", "fr", "ar"):
        for k in ("chat_titel", "chat_hinweis", "chat_senden", "chat_fehler", "chat_limit"):
            assert texte[lang][k]


def test_risk_page_teases_assistant_only_when_enabled(client, ki):
    assert "Nach der Berechnung" in client.get("/risiko").get_data(as_text=True)


def test_risk_page_teaser_also_without_key(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert "Nach der Berechnung" in client.get("/risiko").get_data(as_text=True)


# ---------- kostenloser Hilfe-Assistent (faq.py) ----------

import faq


@pytest.mark.parametrize("lang", ["de", "en", "fr", "ar"])
def test_every_suggestion_chip_gets_its_own_topic(lang):
    ergebnis = {"kategorie": "mittel", "risiko_prozent": 12.3}
    erwartet = {t["label"][lang]: t["antwort"][lang] for t in faq.TOPICS}
    for frage in faq.vorschlaege(lang)[1:]:
        assert faq.antworte(frage, lang, ergebnis) == erwartet[frage]
    antwort = faq.antworte(faq.vorschlaege(lang)[0], lang, ergebnis)
    assert "12.3" in antwort


def test_faq_result_question_without_result():
    assert "Zuerst" in faq.antworte("Was bedeutet mein Ergebnis?", "de")


def test_faq_unknown_question_lists_topics():
    antwort = faq.antworte("Wie wird das Wetter?", "de")
    assert "keine Antwort" in antwort and "Gesamtcholesterin" in antwort


def test_faq_topics_complete_in_all_languages():
    for thema in faq.ALLE:
        for lang in ("de", "en", "fr", "ar"):
            assert thema["label"][lang] and thema["antwort"][lang]


def test_faq_uses_result_from_session(client, monkeypatch, fake_risk):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    client.post("/risiko_berechnen", data=VALID)
    antwort = chat(client, "Was bedeutet mein Ergebnis?").get_json()["antwort"]
    assert "10-Jahres-Risiko" in antwort and "%" in antwort


def test_faq_emergency_still_wins(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert "112" in chat(client, "Brustschmerzen und was ist HDL").get_json()["antwort"]


# ---------- Datenbank-Schicht (SQLite lokal, PostgreSQL mit DATABASE_URL) ----------

import db


def test_tests_never_use_a_real_database_url():
    import os
    assert "DATABASE_URL" not in os.environ and not db.postgres_aktiv()


def test_db_switches_to_postgres_with_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@host/dbname")
    assert db.postgres_aktiv()
    assert db._pg_url() == "postgresql://u:p@host/dbname"      # alte Schreibweise wird angepasst
    assert db._sql("SELECT * FROM t WHERE a = ? AND b = ?") == "SELECT * FROM t WHERE a = %s AND b = %s"
    assert db.id_spalte() == "SERIAL PRIMARY KEY"


def test_db_uses_sqlite_by_default():
    assert db._sql("SELECT ?") == "SELECT ?" and db.id_spalte() == "INTEGER PRIMARY KEY"


def test_db_functions_roundtrip_with_sqlite(tmp_path, monkeypatch):
    import fhir_db
    monkeypatch.chdir(tmp_path)
    fhir_db.erstelle_tabelle(); fhir_db.erstelle_condition_tabelle(); fhir_db.erstelle_risk_score_tabelle()
    pid = fhir_db.patient_hinzufuegen("Zoe", "x"); fhir_db.patient_hinzufuegen("anna", "x")
    fhir_db.condition_hinzufuegen(pid, "Asthma", "Pneumologie")
    fhir_db.risiko_speichern(pid, 55, 220.0, 50.0, 140.0, True, False, 8.3, 15)
    assert [n for _, n in fhir_db.hole_alle_patienten()] == ["anna", "Zoe"]      # alphabetisch, ohne Gross/Klein
    assert fhir_db.hole_patienten_mit_diagnosen()[0][:3] == ("Zoe", "Asthma", "Pneumologie")
    assert fhir_db.hole_neuestes_risiko(pid)[0] == 8.3
    fhir_db.patient_loeschen(pid)
    assert [n for _, n in fhir_db.hole_alle_patienten()] == ["anna"]
