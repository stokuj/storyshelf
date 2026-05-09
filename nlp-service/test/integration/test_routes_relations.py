from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from api.app import app

client = TestClient(app)


class TestRelationsRoute:
    def test_post_relations_returns_202(self):
        """Test that the /books/{bookId}/relations route returns 202 with valid input."""

        with patch(
            "api.routers.relations.process_book_relations_async",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = {"relations": []}
            response = client.post(
                "/books/1/relations",
                json={
                    "bookId": 1,
                    "pairs": [
                        {
                            "pair": ["Frodo", "Sam"],
                            "sentences": ["Frodo and Sam walked."],
                        }
                    ],
                },
            )
        assert response.status_code == 202

    def test_post_relations_missing_sentences_returns_422(self):
        """Test that the /relations/ route returns a 422 status code when the sentences field is missing."""

        response = client.post("/books/1/relations", json={})
        assert response.status_code == 422
        assert response.json()["detail"] == "bookId is required"

    def test_post_relations_missing_name1_returns_422(self):
        """Test that the /relations/ route returns a 422 status code when the name_1 field is missing."""

        response = client.post("/books/1/relations", json={})
        assert response.status_code == 422
        assert response.json()["detail"] == "bookId is required"

    def test_post_relations_missing_name2_returns_422(self):
        """Test that the /relations/ route returns a 422 status code when the name_2 field is missing."""

        response = client.post("/books/1/relations", json={})
        assert response.status_code == 422
        assert response.json()["detail"] == "bookId is required"

    def test_post_relations_whitespace_name_returns_422(self):
        """Test that the /relations/ route returns a 422 when a character name is whitespace only."""

        response = client.post(
            "/books/1/relations",
            json={"bookId": 1, "pairs": []},
        )
        assert response.status_code == 202

    def test_post_relations_same_names_returns_422(self):
        """Test that the /relations/ route returns a 422 when both character names are the same."""

        response = client.post(
            "/books/1/relations",
            json={"bookId": 2, "pairs": []},
        )
        assert response.status_code == 422
        assert response.json()["detail"] == "bookId does not match path"
