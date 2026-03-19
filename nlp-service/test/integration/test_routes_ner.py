from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest
from api.app import app

client = TestClient(app)


class TestNerRoute:
    @pytest.mark.integration
    def test_post_ner_returns_202(self):
        """Test that the chapter ner route returns a 202 status code when given valid input."""

        with patch("api.routers.ner.extract_entities_task.delay") as mock:
            mock.return_value = SimpleNamespace(id="test-task-id")
            response = client.post(
                "/chapters/1/ner",
                json={"chapterId": 1, "content": "Frodo and Sam walked through the Shire."},
            )
        assert response.status_code == 202

    def test_post_ner_missing_content_returns_422(self):
        """Test that the /ner/ route returns a 422 status code when the content field is missing."""

        response = client.post("/chapters/1/ner", json={"chapterId": 1})
        assert response.status_code == 422

    def test_post_ner_whitespace_content_returns_422(self):
        """Test that the /ner/ route returns a 422 status code when the content is whitespace only."""

        response = client.post(
            "/chapters/1/ner", json={"chapterId": 1, "content": "   "}
        )
        assert response.status_code == 422
        assert response.json()["detail"] == "Content cannot be empty"
