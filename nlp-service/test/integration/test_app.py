from unittest.mock import patch

from fastapi.testclient import TestClient

from api.app import app
from api.services.transformers import DEFAULT_NER_MODEL

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_health_returns_200():
    response = client.get("/health/")
    assert response.status_code == 200


def test_health_status_is_ok():
    response = client.get("/health/")
    assert response.json()["status"] == "ok"


def test_health_ner_model_name_matches_default():
    response = client.get("/health/")
    assert response.json()["models"]["ner"]["name"] == DEFAULT_NER_MODEL


def test_health_ner_loaded_true_when_model_loaded():
    with patch("api.app.is_ner_model_loaded", return_value=True):
        response = client.get("/health/")
    assert response.json()["models"]["ner"]["loaded"] is True


def test_health_ner_loaded_false_when_model_not_loaded():
    with patch("api.app.is_ner_model_loaded", return_value=False):
        response = client.get("/health/")
    assert response.json()["models"]["ner"]["loaded"] is False
