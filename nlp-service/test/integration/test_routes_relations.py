from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from api.app import app

client = TestClient(app)


class TestRelationsRoute:
    def test_post_relations_returns_200(self):
        """Test that the /relations/ route returns a 200 status code when given valid input."""

        with patch(
            "api.routers.relations.llm_service.extract_relations",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = '{"relations": []}'
            response = client.post(
                "/relations/",
                json={
                    "name_1": "Frodo",
                    "name_2": "Sam",
                    "sentences": ["Frodo and Sam walked."],
                },
            )
        assert response.status_code == 200

    def test_post_relations_missing_sentences_returns_422(self):
        """Test that the /relations/ route returns a 422 status code when the sentences field is missing."""

        response = client.post("/relations/", json={"name_1": "Frodo", "name_2": "Sam"})
        assert response.status_code == 422

    def test_post_relations_missing_name1_returns_422(self):
        """Test that the /relations/ route returns a 422 status code when the name_1 field is missing."""

        response = client.post(
            "/relations/",
            json={"name_2": "Sam", "sentences": ["Frodo and Sam walked."]},
        )
        assert response.status_code == 422

    def test_post_relations_missing_name2_returns_422(self):
        """Test that the /relations/ route returns a 422 status code when the name_2 field is missing."""

        response = client.post(
            "/relations/",
            json={"name_1": "Frodo", "sentences": ["Frodo and Sam walked."]},
        )
        assert response.status_code == 422

    def test_post_relations_whitespace_name_returns_422(self):
        """Test that the /relations/ route returns a 422 when a character name is whitespace only."""

        response = client.post(
            "/relations/",
            json={
                "name_1": "  ",
                "name_2": "Sam",
                "sentences": ["Frodo and Sam walked."],
            },
        )
        assert response.status_code == 422
        assert response.json()["detail"] == "Character names cannot be empty"

    def test_post_relations_same_names_returns_422(self):
        """Test that the /relations/ route returns a 422 when both character names are the same."""

        response = client.post(
            "/relations/",
            json={
                "name_1": "Frodo",
                "name_2": "Frodo",
                "sentences": ["Frodo and Sam walked."],
            },
        )
        assert response.status_code == 422
        assert response.json()["detail"] == "Character names must be different"
