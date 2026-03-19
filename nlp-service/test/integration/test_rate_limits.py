from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from api.app import app
from api.middleware.rate_limiter import limiter

client = TestClient(app)


@contextmanager
def rate_limit_key(value: str):
    original_key_func = limiter._key_func
    limiter._key_func = lambda request: value
    try:
        yield
    finally:
        limiter._key_func = original_key_func


class TestRateLimitsRelations:
    def test_relations_rate_limit_exceeded_returns_429(self):
        payload = {
            "bookId": 1,
            "pairs": [
                {"pair": ["Frodo", "Sam"], "sentences": ["Frodo and Sam walked."]}
            ],
        }

        with rate_limit_key("rate-limit-relations"):
            with patch(
                "api.routers.relations.process_book_relations_async",
                new_callable=AsyncMock,
            ) as mock:
                mock.return_value = {"relations": []}
                for _ in range(30):
                    response = client.post("/books/1/relations", json=payload)
                    assert response.status_code == 202

                response = client.post("/books/1/relations", json=payload)
                assert response.status_code == 429


class TestRateLimitsNer:
    def test_ner_rate_limit_exceeded_returns_429(self):
        payload = {"chapterId": 1, "content": "Frodo and Sam walked through the Shire."}

        with rate_limit_key("rate-limit-ner"):
            with patch("api.routers.ner.extract_entities_task.delay") as mock:
                mock.return_value = SimpleNamespace(id="test-task-id")
                for _ in range(30):
                    response = client.post("/chapters/1/ner", json=payload)
                    assert response.status_code == 202

                response = client.post("/chapters/1/ner", json=payload)
                assert response.status_code == 429
