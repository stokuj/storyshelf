from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)


class TestFindPairsRoute:
    def test_post_find_pairs_returns_202(self):
        """Test that the /books/{bookId}/find-pairs route returns 202 with valid input."""

        response = client.post(
            "/books/1/find-pairs",
            json={
                "bookId": 1,
                "content": "Bilbo met Gandalf near the Shire. Gandalf spoke with Thorin. Bilbo and Thorin argued about the treasure. Only Gandalf remained calm.",
                "characters": {"Bilbo": 1, "Gandalf": 1, "Thorin": 1},
            },
        )
        assert response.status_code == 202

    def test_post_find_pairs_missing_content_returns_422(self):
        """Test that the /find-pairs/ route returns a 422 status code when the content field is missing."""

        response = client.post("/books/1/find-pairs", json={"bookId": 1})
        assert response.status_code == 422
        assert response.json()["detail"] == "Content cannot be empty"

    def test_post_find_pairs_missing_names_returns_202(self):
        """Test that the endpoint accepts empty characters and still queues work."""

        response = client.post(
            "/books/1/find-pairs",
            json={
                "bookId": 1,
                "content": "Bilbo met Gandalf near the Shire. Gandalf spoke with Thorin. Bilbo and Thorin argued about the treasure. Only Gandalf remained calm.",
            },
        )
        assert response.status_code == 202

    def test_post_find_pairs_whitespace_content_returns_422(self):
        """Test that the /find-pairs/ route returns a 422 status code when the content is whitespace only."""

        response = client.post(
            "/books/1/find-pairs",
            json={"bookId": 1, "content": "   ", "characters": {"Bilbo": 1}},
        )
        assert response.status_code == 422
        assert response.json()["detail"] == "Content cannot be empty"
