# NLP P2 Quality Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 4 quality issues in NLP service: test markers, sentence split regex, tokenizer fallback warning, and request logging middleware.

**Architecture:** Four independent, isolated changes touching 10 files total. Each task modifies a single concern with no cross-dependencies. Run integration tests after each task to verify no regressions.

**Tech Stack:** Python 3.13, FastAPI, pytest, regex

---

## Setup

Before any task, install dependencies in the worktree:

- [ ] **Setup: Install Python dependencies**

```bash
cd nlp-service && uv sync
```

Expected: All dependencies installed, no errors.

---

### Task 1: Mark integration tests and configure pytest filter

**Files:**
- Modify: `nlp-service/pyproject.toml`
- Modify: `nlp-service/test/integration/test_routes_ner.py`
- Modify: `nlp-service/test/integration/test_routes_analyse.py`
- Modify: `nlp-service/test/integration/test_routes_find_pairs.py`
- Modify: `nlp-service/test/integration/test_routes_relations.py`
- Modify: `nlp-service/test/integration/test_routes_app.py`
- Modify: `nlp-service/test/integration/test_rate_limits.py`

- [ ] **Step 1: Add `addopts` filter to pyproject.toml**

In `nlp-service/pyproject.toml`, add `addopts = "-m 'not integration'"` to the `[tool.pytest.ini_options]` section:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
addopts = "-m 'not integration'"
markers = ["integration: requires external services (Redis, Celery)"]
```

- [ ] **Step 2: Add `@pytest.mark.integration` to test_routes_ner.py**

The class `TestNerRoute` already has `@pytest.mark.integration` on one method. Replace with class-level decorator and remove the method-level one:

```python
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest
from api.app import app

client = TestClient(app)


@pytest.mark.integration
class TestNerRoute:
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
```

- [ ] **Step 3: Add `@pytest.mark.integration` to test_routes_analyse.py**

```python
from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest

from api.app import app

client = TestClient(app)


@pytest.mark.integration
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
```

- [ ] **Step 4: Add `@pytest.mark.integration` to test_routes_find_pairs.py**

```python
from fastapi.testclient import TestClient
import pytest

from api.app import app

client = TestClient(app)


@pytest.mark.integration
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
```

- [ ] **Step 5: Add `@pytest.mark.integration` to test_routes_relations.py**

```python
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import pytest
from api.app import app

client = TestClient(app)


@pytest.mark.integration
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

    def test_post_relations_empty_pairs_returns_422(self):
        """Test that the /relations/ route returns a 422 when pairs list is empty."""

        with patch(
            "api.routers.relations.process_book_relations_async",
            new_callable=AsyncMock,
        ) as mock_process:
            mock_process.return_value = {"relations": []}
            response = client.post(
                "/books/1/relations",
                json={"bookId": 1, "pairs": []},
            )
        assert response.status_code == 422
        assert response.json()["detail"] == "pairs list cannot be empty"
        mock_process.assert_not_called()

    def test_post_relations_same_names_returns_422(self):
        """Test that the /relations/ route returns a 422 when both character names are the same."""

        response = client.post(
            "/books/1/relations",
            json={"bookId": 2, "pairs": []},
        )
        assert response.status_code == 422
        assert response.json()["detail"] == "bookId does not match path"
```

- [ ] **Step 6: Add `@pytest.mark.integration` to test_routes_app.py**

Add `import pytest` and decorate all 4 classes:

```python
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
import pytest

from api.app import app

client = TestClient(app)


@pytest.mark.integration
class TestGlobalErrors:
    def test_unhandled_exception_returns_500(self):
        """Test if the global exception handler returns a 500 status code when an unhandled exception occurs."""

        with patch(
            "api.routers.analyse.process_analyse",
            side_effect=RuntimeError("Unexpected error"),
        ):
            with TestClient(app, raise_server_exceptions=False) as c:
                response = c.post(
                    "/chapters/1/analyse", json={"chapterId": 1, "content": "test"}
                )
                assert response.status_code == 500
                assert response.json() == {"detail": "Internal server error"}


@pytest.mark.integration
class TestRoot:
    def test_get_root_returns_200(self):
        """Test if the root endpoint returns a 200 status code and the expected message."""

        response = client.get("/")
        assert response.status_code == 200

    def test_get_root_returns_hello_world(self):
        response = client.get("/")
        assert response.json() == {"message": "Hello World"}


@pytest.mark.integration
class TestHealth:
    def test_get_health_returns_200(self):
        """Test if the /health/ endpoint returns a 200 status code."""

        response = client.get("/health/")
        assert response.status_code == 200

    def test_get_health_returns_status_ok(self):
        """Test if the /health/ endpoint returns a JSON with status 'ok'."""

        response = client.get("/health/")
        assert response.json()["status"] == "ok"

    def test_get_health_includes_required_fields(self):
        """Test if the /health/ endpoint returns a JSON with required fields."""

        response = client.get("/health/")
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "timestamp" in data

    def test_get_health_timestamp_is_iso(self):
        """Test if the /health/ endpoint returns a timestamp in valid ISO format."""

        from datetime import datetime

        response = client.get("/health/")
        timestamp = response.json()["timestamp"]
        datetime.fromisoformat(timestamp)


@pytest.mark.integration
class TestHealthCelery:
    def test_health_celery_returns_200_with_workers(self):
        """Test /health/celery/ returns worker info when Celery is available."""

        mock_inspector = MagicMock()
        mock_inspector.active.return_value = {
            "worker-1": [{"id": "task-1"}],
            "worker-2": [],
        }

        with patch("api.app.celery") as mock_celery:
            mock_celery.control.inspect.return_value = mock_inspector
            response = client.get("/health/celery/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["total_workers"] == 2
        assert data["workers"]["worker-1"]["active_tasks"] == 1
        assert data["workers"]["worker-2"]["active_tasks"] == 0

    def test_health_celery_returns_200_without_workers(self):
        """Test /health/celery/ returns empty workers when none are registered."""

        mock_inspector = MagicMock()
        mock_inspector.active.return_value = {}

        with patch("api.app.celery") as mock_celery:
            mock_celery.control.inspect.return_value = mock_inspector
            response = client.get("/health/celery/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["total_workers"] == 0
        assert data["workers"] == {}

    def test_health_celery_returns_503_on_connection_error(self):
        """Test /health/celery/ returns 503 when Redis connection fails."""

        with patch("api.app.celery") as mock_celery:
            mock_celery.control.inspect.side_effect = ConnectionError(
                "Connection refused"
            )
            response = client.get("/health/celery/")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "error"
        assert "error" in data
```

- [ ] **Step 7: Add `@pytest.mark.integration` to test_rate_limits.py**

Add `import pytest` and decorate both classes:

```python
from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
import pytest

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


@pytest.mark.integration
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


@pytest.mark.integration
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
```

- [ ] **Step 8: Verify integration markers filter correctly**

Run unit tests (should skip all integration tests):

```bash
cd nlp-service && uv run pytest test/unit/ -v
```

Expected: All unit tests pass. No integration tests run.

Run integration tests explicitly:

```bash
cd nlp-service && uv run pytest test/integration/ -v -m integration
```

Expected: All 26 integration tests are collected and run.

- [ ] **Step 9: Commit**

```bash
git add nlp-service/pyproject.toml nlp-service/test/integration/
git commit -m "test: mark integration tests and add pytest filter for unit runs"
```

---

### Task 2: Fix sentence split regex for abbreviations

**Files:**
- Modify: `nlp-service/api/services/core/text_parser.py`

- [ ] **Step 1: Update `SENTENCE_SPLIT_RE` with negative lookbehind**

Replace the regex on line 6 with one that excludes common English abbreviations:

```python
SENTENCE_SPLIT_RE = re.compile(r"(?<!\b(?:Mr|Mrs|Ms|Dr|Prof|Jr|Sr|St|vs))(?<=[.!?])\s+")
```

Leave the rest of the file unchanged.

- [ ] **Step 2: Verify the regex behavior manually**

Run an interactive Python check in the nlp-service directory:

```bash
cd nlp-service && uv run python -c "
import re
pat = re.compile(r'(?<!\b(?:Mr|Mrs|Ms|Dr|Prof|Jr|Sr|St|vs))(?<=[.!?])\s+')

# Should NOT split on abbreviations
assert len(pat.split('Mr. Frodo walked. Sam followed.')) == 2
assert len(pat.split('Dr. Who arrived. Then he left.')) == 2
assert len(pat.split('Mrs. Smith and St. John met.')) == 1

# Should still split on normal sentences
assert len(pat.split('Frodo walked. Sam followed.')) == 2

print('All assertions passed')
"
```

Expected: `All assertions passed`

- [ ] **Step 3: Run unit tests to ensure no regressions**

```bash
cd nlp-service && uv run pytest test/unit/ -v
```

Expected: All unit tests pass.

- [ ] **Step 4: Commit**

```bash
git add nlp-service/api/services/core/text_parser.py
git commit -m "fix: improve sentence split regex to handle abbreviations"
```

---

### Task 3: Add warning on tokenizer fallback

**Files:**
- Modify: `nlp-service/api/services/core/text_stats.py`

- [ ] **Step 1: Add logging import and logger**

Add `import logging` at the top and `logger = logging.getLogger(__name__)`:

```python
from __future__ import annotations

import logging

try:
    import tiktoken
except ImportError:  # pragma: no cover - fallback when optional dep is missing
    tiktoken = None

logger = logging.getLogger(__name__)

TOKENIZER_NAME = "cl100k_base"
_TOKENIZER = None
```

- [ ] **Step 2: Add warning before fallback token count**

In `analyse_text()`, add `logger.warning(...)` inside the `if tokenizer is None:` branch:

```python
def analyse_text(text: str) -> dict:
    """Return analysed text: counts chars, words and tokens."""

    char_count = len(text)
    char_count_clean = sum(ch.isalnum() for ch in text)
    word_count = len(text.split())
    tokenizer = _get_tokenizer()
    if tokenizer is None:
        logger.warning("tiktoken not available, using fallback heuristic (len(text) // 4)")
        token_count = len(text) // 4
    else:
        token_count = len(tokenizer.encode(text))

    return {
        "char_count": char_count,
        "char_count_clean": char_count_clean,
        "word_count": word_count,
        "token_count": token_count,
    }
```

- [ ] **Step 3: Run unit tests to verify no regressions**

```bash
cd nlp-service && uv run pytest test/unit/ -v
```

Expected: All unit tests pass.

- [ ] **Step 4: Commit**

```bash
git add nlp-service/api/services/core/text_stats.py
git commit -m "fix: log warning when tiktoken tokenizer falls back to heuristic"
```

---

### Task 4: Add request logging middleware

**Files:**
- Modify: `nlp-service/api/app.py`

- [ ] **Step 1: Add `import time`**

Add `import time` after `import logging` at line 13 of `app.py`. The top imports should become:

```python
import asyncio
from datetime import UTC, datetime
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import logging
import time
```

- [ ] **Step 2: Add request logging middleware**

Add the middleware function right after `app.add_middleware(CORSMiddleware, ...)` and before the `### Include Routers` comment:

```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    extra = {
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "duration_ms": round(duration * 1000, 2),
    }
    if 400 <= response.status_code:
        logger.warning(
            "Request: %(method)s %(path)s -> %(status)s (%(duration_ms)s ms)", extra
        )
    else:
        logger.debug(
            "Request: %(method)s %(path)s -> %(status)s (%(duration_ms)s ms)", extra
        )
    return response
```

- [ ] **Step 3: Verify middleware placement in app.py**

The middleware should be placed after the existing `app.add_middleware(CORSMiddleware, ...)` call and before the `### Include Routers` comment. Verify the file structure:

```python
app.add_middleware(
    CORSMiddleware,
    ...
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    ...

#####################################################
### Include Routers
#####################################################
app.include_router(analyse_router)
...
```

- [ ] **Step 4: Test middleware works**

Run integration tests to verify no routes break with the new middleware:

```bash
cd nlp-service && uv run pytest test/integration/ -v -m integration
```

Expected: All integration tests pass. The logger.debug messages will appear at the debug level during test runs (if pytest logging is configured).

- [ ] **Step 5: Commit**

```bash
git add nlp-service/api/app.py
git commit -m "feat: add HTTP request logging middleware"
```

---

## Task Order

Tasks 1–4 are independent and can run in any order. If using subagent-driven development, dispatch all 4 in parallel.
