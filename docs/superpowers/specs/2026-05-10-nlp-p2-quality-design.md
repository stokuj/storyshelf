# Design: NLP Service P2 Quality Fixes (Issue #31)

## Summary

4 quality improvements for the NLP service addressing test discipline, sentence splitting accuracy, tokenizer observability, and request logging.

## Changes

### 1. Integration Test Markers

**Context:** 25/26 integration tests in `nlp-service/test/integration/` are missing `@pytest.mark.integration`. The marker is registered in `pyproject.toml` but there is no `addopts` filter to exclude them from unit test runs.

**Fix:**

- **6 test files** — add `@pytest.mark.integration` at the class level for each test class:
  - `test_routes_ner.py` — class `TestNerRoute` (already on one method, remove duplicate method-level marker)
  - `test_routes_analyse.py` — class `TestAnalyseRoute`
  - `test_routes_find_pairs.py` — class `TestFindPairsRoute`
  - `test_routes_relations.py` — class `TestRelationsRoute`
  - `test_routes_app.py` — classes `TestGlobalErrors`, `TestRoot`, `TestHealth`, `TestHealthCelery`
  - `test_rate_limits.py` — classes `TestRateLimitsRelations`, `TestRateLimitsNer`

- **pyproject.toml** — add `addopts = "-m 'not integration'"` to `[tool.pytest.ini_options]`

**Behavior after fix:**
- `pytest` runs only unit tests
- `pytest -m integration` runs integration tests
- `pytest -m ""` or `pytest -m "not integration or integration"` runs all tests

### 2. Sentence Split Regex for Abbreviations

**Context:** `text_parser.py:6` — `SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")` splits on every period, incorrectly breaking on abbreviations like "Mr.", "Dr.", "vs.", etc.

**Fix:** Add negative lookbehind for common English abbreviations:

```python
SENTENCE_SPLIT_RE = re.compile(
    r"(?<!\b(?:Mr|Mrs|Ms|Dr|Prof|Jr|Sr|St|vs))(?<=[.!?])\s+"
)
```

Abbreviation list: Mr, Mrs, Ms, Dr, Prof, Jr, Sr, St, vs (case-sensitive to avoid false negatives on all-caps text).

**Impact:** Sentences containing "Mr. Frodo", "Dr. Who", "St. Mary" etc. will no longer be split mid-sentence.

### 3. Tokenizer Fallback Warning

**Context:** `text_stats.py:27` — when `tiktoken` is unavailable, the code silently falls back to `len(text) // 4`. There is no indication that the heuristic is being used instead of proper tokenization.

**Fix:** Add a logger and emit a warning when the fallback path is taken:

```python
import logging

logger = logging.getLogger(__name__)

def analyse_text(text: str) -> dict:
    ...
    if tokenizer is None:
        logger.warning("tiktoken not available, using fallback heuristic (len(text) // 4)")
        token_count = len(text) // 4
    ...
```

Only the first call to `analyse_text` actually hits `_TOKENIZER is None` check (after `_get_tokenizer()` caches the failure). The warning fires every time tokenizer is unavailable.

### 4. Request Logging Middleware

**Context:** `app.py` has `SlowAPIMiddleware` and `CORSMiddleware` but no request/response logging. Debugging production issues requires visibility into incoming requests.

**Fix:** Add an `@app.middleware("http")` that logs each request:

```python
import time

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

**Log levels:**
- 2xx responses → `logger.debug` (noise-free production logs)
- 4xx/5xx responses → `logger.warning` (visible by default)

## Files Modified

| File | Change |
|------|--------|
| `nlp-service/test/integration/test_routes_ner.py` | Add `@pytest.mark.integration` at class level |
| `nlp-service/test/integration/test_routes_analyse.py` | Add `@pytest.mark.integration` at class level |
| `nlp-service/test/integration/test_routes_find_pairs.py` | Add `@pytest.mark.integration` at class level |
| `nlp-service/test/integration/test_routes_relations.py` | Add `@pytest.mark.integration` at class level |
| `nlp-service/test/integration/test_routes_app.py` | Add `@pytest.mark.integration` to 4 test classes |
| `nlp-service/test/integration/test_rate_limits.py` | Add `@pytest.mark.integration` to 2 test classes |
| `nlp-service/pyproject.toml` | Add `addopts = "-m 'not integration'"` |
| `nlp-service/api/services/core/text_parser.py` | Improve `SENTENCE_SPLIT_RE` with abbreviation negative lookbehind |
| `nlp-service/api/services/core/text_stats.py` | Add `logger.warning()` on tokenizer fallback |
| `nlp-service/api/app.py` | Add request logging middleware |

## Non-Goals

- No new unit tests (out of scope for P2)
- No configurable abbreviation list
- No changes to Kafka or LLM error logging (already fixed in #22)
