"""Tests for the MediLink Flask app. Run with: py -m pytest -v"""
import re

import pytest
import app as app_module
from app import app
from translations import texte, diagnose_uebersetzung, kategorie_uebersetzung, KATEGORIEN, DIAGNOSEN, ANDERE

VALID = {"name": "Demo", "sex": "m", "alter": "55", "cholesterin": "220",
         "hdl": "50", "blutdruck": "140", "lang": "de"}


@pytest.fixture
def client():
    """A fake browser that sends requests to the app without starting a server."""
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def fake_db(monkeypatch):
    """Replace the database functions so tests never touch the real patienten.db."""
    saved = []
    monkeypatch.setattr(app_module, "patient_hinzufuegen",
                        lambda name, text: saved.append(name) or 99)
    monkeypatch.setattr(app_module, "condition_hinzufuegen",
                        lambda patient_id, diagnose, kategorie: None)
    monkeypatch.setattr(app_module, "risiko_speichern", lambda *args: None)
    return saved


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
    assert response.status_code == 200
    assert "erfolgreich gespeichert" in response.get_data(as_text=True)
    assert fake_db == ["Test Patient"]


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


def test_valid_input_saves_once_and_shows_result(client, fake_db):
    response = post_risk(client)
    assert response.status_code == 200
    assert re.search(r"Risiko berechnet: \d+\.\d%", response.get_data(as_text=True))
    assert fake_db == ["Demo"]


def test_result_is_in_selected_language(client, fake_db):
    html = post_risk(client, lang="fr").get_data(as_text=True)
    assert "Risque calculé" in html and "Risiko berechnet" not in html


@pytest.mark.parametrize("feld,wert", [
    ("hdl", "5"), ("hdl", "150"), ("cholesterin", "50"), ("cholesterin", "900"),
    ("blutdruck", "300"), ("blutdruck", "20"), ("alter", "20"), ("alter", "95"),
])
def test_out_of_range_is_rejected_and_nothing_is_saved(client, fake_db, feld, wert):
    response = post_risk(client, **{feld: wert})
    assert response.status_code == 400
    assert fake_db == []                      # kein Patient ohne Score
    html = response.get_data(as_text=True)
    assert 'class="fehler"' in html and "muss zwischen" in html
    assert f'value="{wert}"' in html          # Eingabe bleibt erhalten


def test_error_message_is_in_selected_language(client, fake_db):
    html = post_risk(client, hdl="5", lang="fr").get_data(as_text=True)
    assert "doit être compris entre 20 et 100" in html
    html = post_risk(client, hdl="5", lang="ar").get_data(as_text=True)
    assert "بين 20 و100" in html


def test_empty_and_non_numeric_fields_rejected(client, fake_db):
    assert post_risk(client, hdl="").status_code == 400
    assert post_risk(client, hdl="abc").status_code == 400
    assert post_risk(client, hdl="nan").status_code == 400
    assert post_risk(client, alter="55.5").status_code == 400
    assert post_risk(client, name="   ").status_code == 400
    assert post_risk(client, sex="x").status_code == 400
    assert fake_db == []


def test_hdl_must_be_lower_than_total_cholesterol(client, fake_db):
    response = post_risk(client, cholesterin="100", hdl="100")   # beide im Bereich, aber unlogisch
    assert response.status_code == 400
    assert "HDL muss kleiner" in response.get_data(as_text=True)
    assert fake_db == []


def test_decimal_comma_is_accepted(client, fake_db):
    assert post_risk(client, cholesterin="220,5").status_code == 200


def test_error_page_language_switch_uses_get_route(client, fake_db):
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
    assert post_patient(client, diagnose="Schlaganfall").status_code == 200
    assert gespeichert == ["Schlaganfall"]


def test_other_diagnosis_uses_free_text(client, monkeypatch, fake_db):
    gespeichert = []
    monkeypatch.setattr(app_module, "condition_hinzufuegen",
                        lambda pid, diagnose, kategorie: gespeichert.append(diagnose))
    response = post_patient(client, diagnose=ANDERE, diagnose_frei="  Gicht ")
    assert response.status_code == 200 and gespeichert == ["Gicht"]


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
