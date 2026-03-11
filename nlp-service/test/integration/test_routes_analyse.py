from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)


class TestAnalyseRoute:
    def test_post_analyse_returns_200(self):
        """Test that the /analyse/ route returns a 200 status code when given valid input."""

        response = client.post("/analyse/", json={"content": "Frodo and Sam walked."})
        assert response.status_code == 200

    def test_post_analyse_missing_content_returns_422(self):
        """Test that the /analyse/ route returns a 422 status code when the content field is missing."""

        response = client.post("/analyse/", json={})
        assert response.status_code == 422
        assert response.json()["detail"] == "Content cannot be empty"

    def test_post_analyse_whitespace_content_returns_422(self):
        """Test that the /analyse/ route returns a 422 status code when the content is whitespace only."""

        response = client.post("/analyse/", json={"content": "   "})
        assert response.status_code == 422
        assert response.json()["detail"] == "Content cannot be empty"
