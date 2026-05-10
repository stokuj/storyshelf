# NLP Service P1 Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix three P1 bugs in the NLP service: remove dead Celery task, add empty pairs validation, fix event-loop blocking in analyse endpoint.

**Architecture:** Three independent fixes in `nlp-service/` on branch `fix/nlp-service-p1-22`. Each task changes 1-2 files. Tests exist for all affected endpoints.

**Tech Stack:** FastAPI, Celery, pytest, asyncio

**Spec:** `docs/superpowers/specs/2026-05-09-nlp-service-fixes-design.md`

---

### Task 1: Remove dead `relations_task` Celery task

**Files:**
- Delete: `nlp-service/api/tasks/relations_task.py`
- Modify: `nlp-service/api/config/celery_app.py:12`

- [ ] **Step 1: Delete the dead task file**

```bash
rm nlp-service/api/tasks/relations_task.py
```

- [ ] **Step 2: Remove from Celery `include` list**

In `nlp-service/api/config/celery_app.py`, change line 12 from:

```python
    include=["api.tasks.ner_task", "api.tasks.relations_task", "api.tasks.find_pairs_task"],
```

to:

```python
    include=["api.tasks.ner_task", "api.tasks.find_pairs_task"],
```

- [ ] **Step 3: Verify Celery config loads without errors**

```bash
cd nlp-service && PYTHONPATH=. uv run python -c "from api.config.celery_app import celery; print('OK:', celery.main)" 2>&1
```

Expected: Prints `OK: app` with no import errors.

- [ ] **Step 4: Commit**

```bash
git add nlp-service/api/tasks/relations_task.py nlp-service/api/config/celery_app.py
git commit -m "fix(nlp): remove dead relations_task Celery task (never called)"
```

---

### Task 2: Add empty pairs validation in relations router

**Files:**
- Modify: `nlp-service/api/routers/relations.py:28-29`
- Modify: `nlp-service/test/integration/test_routes_relations.py:52-59`

- [ ] **Step 1: Add failing test for empty pairs**

In `nlp-service/test/integration/test_routes_relations.py`, replace the whitespace_name test (lines 52-59) with:

```python
    def test_post_relations_empty_pairs_returns_422(self):
        """Test that the /relations/ route returns a 422 when pairs list is empty."""

        response = client.post(
            "/books/1/relations",
            json={"bookId": 1, "pairs": []},
        )
        assert response.status_code == 422
        assert response.json()["detail"] == "pairs list cannot be empty"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd nlp-service && uv run pytest test/integration/test_routes_relations.py::TestRelationsRoute::test_post_relations_empty_pairs_returns_422 -v 2>&1
```

Expected: FAIL with `AssertionError: assert 202 == 422`

- [ ] **Step 3: Add validation in router**

In `nlp-service/api/routers/relations.py`, after line 26 (the bookId check), add:

```python
    if not payload.pairs:
        raise HTTPException(status_code=422, detail="pairs list cannot be empty")
```

The full endpoint body should now look like:

```python
async def relations(
    request: Request, bookId: int | str, payload: BookRelationsPayload
) -> AcceptedResponse:
    if str(payload.bookId) != str(bookId):
        raise HTTPException(status_code=422, detail="bookId does not match path")

    if not payload.pairs:
        raise HTTPException(status_code=422, detail="pairs list cannot be empty")

    pairs = [pair.model_dump() for pair in payload.pairs]
    task = asyncio.create_task(process_book_relations_async(pairs, bookId))
    ...
```

- [ ] **Step 4: Run all relations tests to verify**

```bash
cd nlp-service && uv run pytest test/integration/test_routes_relations.py -v 2>&1
```

Expected: All tests PASS. Note that `test_post_relations_same_names_returns_422` (bookId mismatch, also uses empty pairs) still passes because the bookId check fires first.

- [ ] **Step 5: Commit**

```bash
git add nlp-service/api/routers/relations.py nlp-service/test/integration/test_routes_relations.py
git commit -m "fix(nlp): reject empty pairs list in relations endpoint with 422"
```

---

### Task 3: Fix analyse endpoint event-loop blocking

**Files:**
- Modify: `nlp-service/api/routers/analyse.py`

- [ ] **Step 1: Run existing analyse tests to confirm they pass before changes**

```bash
cd nlp-service && uv run pytest test/integration/test_routes_analyse.py -v 2>&1
```

Expected: All 3 tests PASS.

- [ ] **Step 2: Convert endpoint to async and offload blocking call**

In `nlp-service/api/routers/analyse.py`:

(a) Add `import asyncio` at line 1:

```python
import asyncio

from fastapi import APIRouter, HTTPException
```

(b) Change the endpoint from `def` to `async def` and wrap `process_analyse` in `asyncio.to_thread()`:

```python
@router.post(
    "/{chapterId}/analyse",
    summary="Calculate text statistics",
    description="Synchronously calculates character counts, word counts, and token counts for a given chapter content.",
    response_model=AcceptedResponse,
    status_code=202,
)
async def analyse_text_endpoint(
    chapterId: int | str, payload: ChapterContentPayload
) -> AcceptedResponse:
    if not payload.content.strip():
        raise HTTPException(status_code=422, detail="Content cannot be empty")
    if str(payload.chapterId) != str(chapterId):
        raise HTTPException(status_code=422, detail="chapterId does not match path")

    await asyncio.to_thread(process_analyse, payload.content, chapter_id=chapterId)
    return AcceptedResponse(status="accepted")
```

The full final file:

```python
import asyncio

from fastapi import APIRouter, HTTPException
from api.models.model import AcceptedResponse, ChapterContentPayload
from api.services import process_analyse

router = APIRouter(prefix="/chapters", tags=["analyse"])


@router.post(
    "/{chapterId}/analyse",
    summary="Calculate text statistics",
    description="Synchronously calculates character counts, word counts, and token counts for a given chapter content.",
    response_model=AcceptedResponse,
    status_code=202,
)
async def analyse_text_endpoint(
    chapterId: int | str, payload: ChapterContentPayload
) -> AcceptedResponse:
    if not payload.content.strip():
        raise HTTPException(status_code=422, detail="Content cannot be empty")
    if str(payload.chapterId) != str(chapterId):
        raise HTTPException(status_code=422, detail="chapterId does not match path")

    await asyncio.to_thread(process_analyse, payload.content, chapter_id=chapterId)
    return AcceptedResponse(status="accepted")
```

- [ ] **Step 3: Run analyse tests to verify they still pass**

```bash
cd nlp-service && uv run pytest test/integration/test_routes_analyse.py -v 2>&1
```

Expected: All 3 tests PASS (tests patch `process_analyse` at import time; `asyncio.to_thread()` calls the mocked function in a thread, returning the mock's `return_value`).

- [ ] **Step 4: Run full test suite to check nothing broke**

```bash
cd nlp-service && uv run pytest -v 2>&1
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add nlp-service/api/routers/analyse.py
git commit -m "fix(nlp): offload blocking process_analyse to thread in async endpoint"
```
