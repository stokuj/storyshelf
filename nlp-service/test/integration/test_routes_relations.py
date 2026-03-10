#test_routes_relations.py

from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from api.app import app

client = TestClient(app)


def test_route_returns_200():
    """Test that the /relations/ route returns a 200 status code when given valid input."""

    with patch("api.routers.relations.llm_service.extract_relations", new_callable=AsyncMock) as mock:
        mock.return_value = '{"relations": []}'
        response = client.post("/relations/", json={
            "name_1": "Frodo",
            "name_2": "Sam",
            "sentences": ["Frodo and Sam walked."]
        })
    assert response.status_code == 200


def test_route_missing_sentences_returns_422():
    """Test that the /relations/ route returns a 422 status code when the sentences field is missing."""

    response = client.post("/relations/", json={"name_1": "Frodo", "name_2": "Sam"})
    assert response.status_code == 422


def test_route_missing_name_1_returns_422():
    """Test that the /relations/ route returns a 422 status code when the name_1 field is missing."""

    response = client.post("/relations/", json={"name_2": "Sam", "sentences": ["Frodo and Sam walked."]})
    assert response.status_code == 422


def test_route_missing_name_2_returns_422():
    """Test that the /relations/ route returns a 422 status code when the name_2 field is missing."""

    response = client.post("/relations/", json={"name_1": "Frodo", "sentences": ["Frodo and Sam walked."]})
    assert response.status_code == 422

