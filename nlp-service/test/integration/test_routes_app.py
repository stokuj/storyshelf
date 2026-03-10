#test_routes_app.py
from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)


def test_root():
    """Test if the root endpoint returns a 200 status code and the expected message."""

    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_health_returns_200():
    """Test if the /health/ endpoint returns a 200 status code."""

    response = client.get("/health/")
    assert response.status_code == 200


def test_health_status_is_ok():
    """Test if the /health/ endpoint returns a JSON with status 'ok'."""

    response = client.get("/health/")
    assert response.json()["status"] == "ok"

def test_health_contains_required_fields():
    """Test if the /health/ endpoint returns a JSON with required fields."""

    response = client.get("/health/")
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "timestamp" in data

def test_health_timestamp_is_valid_iso():
    """Test if the /health/ endpoint returns a timestamp in valid ISO format."""

    from datetime import datetime
    response = client.get("/health/")
    timestamp = response.json()["timestamp"]
    datetime.fromisoformat(timestamp)

