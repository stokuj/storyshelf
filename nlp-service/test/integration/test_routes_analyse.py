from fastapi.testclient import TestClient
from unittest.mock import patch

from api.app import app

client = TestClient(app)


class TestAnalyseRoute:
    def test_post_analyse_returns_202(self):
        """Test that the chapter analyse route returns 202 with valid input."""

        with patch("api.routers.analyse.process_analyse") as mock:
            mock.return_value = {"char_count": 1}
            response = client.post(
                "/chapters/1/analyse",
                json={"chapterId": 1, "content": "Frodo and Sam walked."},
            )
        assert response.status_code == 202

    def test_post_analyse_missing_content_returns_422(self):
        """Test that the /analyse/ route returns a 422 status code when the content field is missing."""

        response = client.post("/chapters/1/analyse", json={"chapterId": 1})
        assert response.status_code == 422
        assert response.json()["detail"] == "Content cannot be empty"

    def test_post_analyse_whitespace_content_returns_422(self):
        """Test that the /analyse/ route returns a 422 status code when the content is whitespace only."""

        response = client.post(
            "/chapters/1/analyse", json={"chapterId": 1, "content": "   "}
        )
        assert response.status_code == 422
        assert response.json()["detail"] == "Content cannot be empty"
