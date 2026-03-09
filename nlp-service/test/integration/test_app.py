from unittest.mock import patch

from fastapi.testclient import TestClient

from api.app import app
from api.services.transformers_service import DEFAULT_NER_MODEL

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

