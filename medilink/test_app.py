"""Tests for the MediLink Flask app. Run with: py -m pytest -v"""
import pytest
import app as app_module
from app import app


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
    return saved


def test_form_page_loads(client):
    response = client.get("/neu")
    assert response.status_code == 200


def test_add_patient_shows_confirmation(client, fake_db):
    response = client.post("/hinzufuegen", data={
        "name": "Test Patient",
        "diagnose": "Hypertonie",
        "kategorie": "Kardiologie",
    })
    assert response.status_code == 200
    assert "erfolgreich gespeichert" in response.get_data(as_text=True)
    assert fake_db == ["Test Patient"]   # the patient was passed to the "database"
