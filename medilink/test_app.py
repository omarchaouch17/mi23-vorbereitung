"""Tests for the MediLink Flask app. Run with: py -m pytest -v"""
import re

import pytest
import app as app_module
from app import app
from translations import texte, diagnose_uebersetzung, kategorie_uebersetzung, KATEGORIEN, DIAGNOSEN, ANDERE

VALID = {"patient_id": "1", "sex": "m", "alter": "55", "cholesterin": "220",
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


@pytest.fixture(autouse=True)
def fake_patienten(monkeypatch):
    """Vorhandene Patienten fuer die Auswahlliste im Risiko-Formular (nie die echte Datenbank)."""
    monkeypatch.setattr(app_module, "hole_patienten_liste", lambda: [(2, "Anna"), (1, "Demo")])


@pytest.fixture
def fake_risk(monkeypatch):
    """Merkt sich, zu welchen Patienten ein Score gespeichert wird."""
    gespeichert = []
    monkeypatch.setattr(app_module, "risiko_speichern",
                        lambda patient_id, *args: gespeichert.append(patient_id))
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
