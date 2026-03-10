#test_routes_ner.py

from fastapi.testclient import TestClient
import pytest
from api.app import app

client = TestClient(app)


@pytest.mark.integration
def test_route_returns_202():
    """Test that the /ner/ route returns a 202 status code when given valid input."""

    response = client.post("/ner/", json={"content": "Frodo and Sam walked through the Shire."})
    assert response.status_code == 202
    assert "task_id" in response.json()


def test_route_missing_content_returns_422():
    """Test that the /ner/ route returns a 422 status code when the content field is missing."""

    response = client.post("/ner/", json={})
    assert response.status_code == 422


@pytest.mark.integration
def test_get_task_status():
    """Test that the /ner/{task_id} route returns a 200 status code when given a valid task ID."""

    # First, create a new NER task
    response = client.post("/ner/", json={"content": "Frodo and Sam walked through the Shire."})
    task_id = response.json().get("task_id")

    # Now, check the state of the task
    response = client.get(f"/ner/{task_id}")
    data = response.json()

    assert "state" in data  # PENDING / SUCCESS / FAILURE
    assert response.status_code == 200


def test_get_task_status_invalid_id():
    """Unknown task_id returns 200 with PENDING status"""
    """Celery cannot distinguish non-existent from pending."""

    response = client.get("/ner/nonexistent-task-id")
    assert response.status_code == 200
    assert response.json()["state"] == "PENDING"
