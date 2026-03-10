from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)


def test_route_returns_200():
    """Test that the /analyse/ route returns a 200 status code when given valid input."""

    response = client.post("/analyse/", json={"content": "Frodo and Sam walked."})
    assert response.status_code == 200


def test_route_missing_content_returns_422():
    """Test that the /analyse/ route returns a 422 status code when the content field is missing."""

    response = client.post("/analyse/", json={})
    assert response.status_code == 422
