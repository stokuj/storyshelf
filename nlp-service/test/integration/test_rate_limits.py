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
            "name_1": "Frodo",
            "name_2": "Sam",
            "sentences": ["Frodo and Sam walked."],
        }

        with rate_limit_key("rate-limit-relations"):
            with patch(
                "api.routers.relations.llm_service.extract_relations",
                new_callable=AsyncMock,
            ) as mock:
                mock.return_value = '{"relations": []}'
                for _ in range(10):
                    response = client.post("/relations/", json=payload)
                    assert response.status_code == 200

                response = client.post("/relations/", json=payload)
                assert response.status_code == 429


class TestRateLimitsNer:
    def test_ner_rate_limit_exceeded_returns_429(self):
        payload = {"content": "Frodo and Sam walked through the Shire."}

        with rate_limit_key("rate-limit-ner"):
            with patch("api.routers.ner.extract_entities_task.delay") as mock:
                mock.return_value = SimpleNamespace(id="test-task-id")
                for _ in range(5):
                    response = client.post("/ner/", json=payload)
                    assert response.status_code == 202

                response = client.post("/ner/", json=payload)
                assert response.status_code == 429
