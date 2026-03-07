from unittest.mock import patch

from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)


def test_route_returns_200():
    response = client.post("/find-pairs/", json={"content": "Frodo and Sam walked.", "names": ["Frodo", "Sam"]})
    assert response.status_code == 200

def test_route_missing_content_returns_422():
    response = client.post("/find-pairs/", json={"names": ["Frodo"]})
    assert response.status_code == 422

def test_route_missing_names_returns_422():
    response = client.post("/find-pairs/", json={"content": "Frodo and Sam walked."})
    assert response.status_code == 422
