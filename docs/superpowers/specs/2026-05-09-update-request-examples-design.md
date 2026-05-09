# Design: Update REQUEST_EXAMPLES.md paths to match actual routers

## Summary

`nlp-service/docs/REQUEST_EXAMPLES.md` references endpoint paths that no longer exist in the codebase. The document must be rewritten to reflect the current API structure where routes use `/chapters/{chapterId}/` and `/books/{bookId}/` prefixed paths.

## Current State

REQUEST_EXAMPLES.md documents these non-existent paths:
- `POST /analyse/`
- `POST /find-pairs/`
- `POST /ner/`
- `GET /ner/{task_id}` — endpoint does not exist in code
- `POST /relations/`
- `GET /health/` — this one is correct

Actual API endpoints (7 total):
| Path | Method | Router/File |
|---|---|---|
| `/` | GET | app.py (top-level) |
| `/health/` | GET | app.py (top-level) |
| `/health/celery/` | GET | app.py (top-level) |
| `/chapters/{chapterId}/analyse` | POST | analyse.py |
| `/chapters/{chapterId}/ner` | POST | ner.py (rate limited 30/min) |
| `/books/{bookId}/find-pairs` | POST | find_pairs.py |
| `/books/{bookId}/relations` | POST | relations.py (rate limited 30/min) |

Payload differences:
- Old: flat payloads without IDs (e.g., `{"content": "...", "names": [...]}`)
- New: all POST payloads include `chapterId` or `bookId` field that must match the URL path parameter; mismatches return 422
- `find-pairs` uses `characters` (dict) instead of `names` (list)
- `relations` uses `pairs` (array of `{pair: [str, str], sentences: [str]}`) instead of `name_1`, `name_2`, `sentences`

Response differences:
- Old: endpoints returned computed data inline (e.g., `analysis`, `pairs`, `relations`)
- New: all POST endpoints return `202 { "status": "accepted" }` — processing is async or fire-and-forget

`GET /ner/{task_id}` has no equivalent in the current codebase and must be removed entirely.

## Design

### Document Structure (Option B — routing groups)

```
# API Testing Guide — Swagger UI

Overview paragraph explaining the routing model:
- Health endpoints (top-level)
- Chapters endpoints: /chapters/{chapterId}/...
- Books endpoints: /books/{bookId}/...

## 1. Health Endpoints
  - GET /
  - GET /health/
  - GET /health/celery/

## 2. Chapters Endpoints
  Common note: chapterId in URL must match chapterId in payload.
  - POST /chapters/{chapterId}/analyse (placeholder ID used in examples)
  - POST /chapters/{chapterId}/ner (placeholder ID used in examples)

## 3. Books Endpoints
  Common note: bookId in URL must match bookId in payload.
  - POST /books/{bookId}/find-pairs (placeholder ID used in examples)
  - POST /books/{bookId}/relations (placeholder ID used in examples)

## 4. Common Errors
  422 ID mismatch, 422 empty content, 422 missing field, 429 rate limit

## 5. Testing Workflow
  Recommended order, tips

## 6. Notes
  Async NER via Celery, relations via LLM, find-pairs via thread pool
```

### Section Details

**Health Endpoints** — 3 subsections, each with purpose, Swagger UI steps, expected response.

**Chapters Endpoints** — opens with a shared box/note about `chapterId` validation (`chapterId` in URL must match `chapterId` in payload → else 422). Then 2 subsections: `/analyse` and `/ner`.

**Books Endpoints** — opens with a shared box/note about `bookId` validation. Then 2 subsections: `/find-pairs` and `/relations`.

**Common Errors** — a table or bullet list of error scenarios, HTTP codes, and causes.

**Testing Workflow** — updated recommended order: Health → Chapters → Books. Tips unchanged.

**Notes** — removes `GET /ner/{task_id}` mention. Keeps NER async, relations LLM, find-pairs thread pool notes.

### Examples

All examples use concrete ID values (`1` or `42`) for both URL and payload so users can copy-paste directly into Swagger UI.

### Removals
- Entire `GET /ner/{task_id}` section (endpoint does not exist)
- All old response structures that showed computed data (replace with `202 { "status": "accepted" }`)
- `names` field references (replaced with `characters` dict for find-pairs)
- `name_1`/`name_2` flat fields (replaced with `pairs` array for relations)

### Additions
- `GET /` section
- `GET /health/celery/` section
- Common Errors section
- Routing model overview in the introduction

## Verification

- Compare every path in REQUEST_EXAMPLES.md against the router files (`analyse.py`, `ner.py`, `find_pairs.py`, `relations.py`, `app.py`)
- Verify payload schemas match `api/models/model.py`
- Verify response codes match actual endpoint behavior (202 for POSTs)
- Run integration tests: `pytest nlp-service/test/integration/`
