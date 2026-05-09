# NLP Service Fixes — Design Spec

**Issue:** [#22](https://github.com/stokuj/storyshelf/issues/22)
**Date:** 2026-05-09
**Scope:** `nlp-service/`

## Summary

Three P1 bugs in the NLP service: a dead Celery task, missing validation for empty input, and an event-loop blocking call.

## Bug 1: Dead Celery task — `extract_chapter_relations_task`

### Problem

`api/tasks/relations_task.py:9-18` defines a Celery task that is registered in `celery_app.py`'s `include` list but has **zero call sites** anywhere in the codebase (no `.delay()` or `.apply_async()` call). The task wraps `process_chapter_relations()` — a workflow function that itself is never called.

### Fix

- **Delete** `api/tasks/relations_task.py` entirely.
- **Remove** `"api.tasks.relations_task"` from the `include` list in `api/config/celery_app.py:12`.

The existing code paths for relations (HTTP router and Kafka consumer) both use `process_book_relations_async()` directly, which is the correct async path. No replacement needed.

## Bug 2: Empty `pairs` list accepted silently

### Problem

`api/routers/relations.py:22-28` accepts a `POST /books/{id}/relations` request with `pairs: []` and returns 202 — but no actual work is done. `process_book_relations_async` runs `asyncio.gather()` with no coroutines (returns empty list), a Kafka message with `all_relations: []` is sent, and the client gets a misleading success response.

Other routers (`analyse.py`, `ner.py`, `find_pairs.py`) all validate non-empty content with `if not payload.content.strip(): raise HTTPException(422, ...)`. This validation is missing in the relations router.

### Fix

Add validation **before** `asyncio.create_task`:

```python
if not payload.pairs:
    raise HTTPException(status_code=422, detail="pairs list cannot be empty")
```

Update the existing test in `test/integration/test_routes_relations.py:59` to expect `422` instead of `202` for the empty pairs case.

## Bug 3: `analyse` endpoint blocks the event loop

### Problem

`api/routers/analyse.py:23` calls `process_analyse()` synchronously via a `def` endpoint. `process_analyse` internally calls `_producer.flush()` — a **blocking Kafka network I/O call** — which blocks the entire async event loop thread for every request.

### Fix

Convert the endpoint from `def` to `async def` and offload the blocking call:

```python
@router.post(...)
async def analyse_text_endpoint(...) -> AcceptedResponse:
    ...
    await asyncio.to_thread(process_analyse, payload.content, chapter_id=chapterId)
    return AcceptedResponse(status="accepted")
```

Using `asyncio.to_thread()` (Python 3.9+) — cleaner API than the `loop.run_in_executor()` pattern already used in `find_pairs.py`.

## Impact

| Change | Breaking? | Notes |
|--------|-----------|-------|
| Delete relations_task.py | No | Never called, no consumers |
| Remove from Celery include | No | Just an import that was never used |
| Empty pairs → 422 | **Yes** — HTTP status change | Previously 202 for empty pairs. If any client sends empty pairs, they now get 422 instead of silent success. |
| analyse async offload | No | Response format unchanged, status unchanged |
| Test expectation change | Internal | Matches the new validation behavior |

## Worktree Strategy

A dedicated git worktree will isolate this work from other concurrent tasks (other opencode windows working on different issues). Branch name: `fix/nlp-service-p1-22`.
