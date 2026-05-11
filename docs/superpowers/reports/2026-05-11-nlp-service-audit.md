# NLP Service Audit Report — 2026-05-11

## Executive Summary

The NLP service (`storyweave` v0.9.1) provides four endpoints for text analysis,
NER, character-pair discovery, and LLM-powered relation extraction. It handles
asynchronous work through Celery tasks and fire-and-forget background jobs, and
reports results back to Django via HTTP callbacks.

The principal risk is **silent data loss**: three of four endpoints use
unobservable fire-and-forget execution, and callback failures are swallowed
without surfacing to callers. Additionally, LLM errors are silently converted to
empty results — indistinguishable from genuine "no relationship found" — and
`asyncio.gather` default exception behavior cancels all remaining extractions
when any single pair fails. Import-time side effects make the service fragile
at startup and in tests.

The service is **not production-safe** in its current state. Remediation
requires making background execution observable, hardening the callback path,
and validating LLM outputs before forwarding to Django.

---

## Findings

| # | Severity | Area | Description | Evidence | Recommendation |
|---|----------|------|-------------|----------|----------------|
| 1 | HIGH | Async | Fire-and-forget execution in 3 of 4 endpoints — caller receives 202 before work is verified, no failure feedback | `nlp-service/api/routers/find_pairs.py:31`, `nlp-service/api/routers/relations.py:32`, `nlp-service/api/routers/ner.py:25` | Return a job/request ID in every 202 response. Add `GET /jobs/{jobId}/status` endpoint exposing Celery task state and executor/coroutine status |
| 2 | HIGH | Callback | `send_json` swallows HTTP callback failures — NLP results are computed but never delivered to Django; no dead-letter queue | `nlp-service/api/kafka/producer.py:37-43`, all 4 workflow files | Use Celery tasks for all callbacks with persistent retry. Write failed callbacks to a dead-letter log file as JSON Lines |
| 3 | HIGH | LLM | `LLMService` catches 5 OpenAI exception types and returns `'{"relations": []}'` — caller receives empty relations without knowing extraction failed | `nlp-service/api/services/core/llm_engine.py:139-146`, `:173-180` | Return distinguishable error values (e.g. `{"error": "rate_limit"}`) instead of empty relations. Propagate error metadata through callback to Django |
| 4 | HIGH | LLM | LLM JSON output is not semantically validated — hallucinated evidence, invalid relation types, and out-of-scope characters flow unchecked to Django | `nlp-service/api/services/core/llm_engine.py:60-103`, `nlp-service/api/services/workflows/relations_workflow.py:81-83` | Validate evidence substrings against input sentences, relation types against `RELATION_SCHEMA`, and character names against requested pair. Add `json_parse_error` flag to results |
| 5 | HIGH | Async | `asyncio.gather` uses default `return_exceptions=False` — a single LLM failure in a batch cancels all remaining extractions; partial results lost and no callback sent | `nlp-service/api/services/workflows/relations_workflow.py:111` | Use `asyncio.gather(..., return_exceptions=True)` to collect partial results. Process results vs. exceptions separately and send succeeded items via callback |
| 6 | MEDIUM | Startup | `LLMService()` instantiated at module import — any env misconfiguration breaks imports before FastAPI starts | `nlp-service/api/services/core/llm_engine.py:183` | Convert to lazy singleton via `@lru_cache` factory or FastAPI `on_startup` hook |
| 7 | MEDIUM | NER | NER model loaded at Celery worker init — if model download fails, workers start but every NER task returns `{}`; no health check validates model availability | `nlp-service/api/config/celery_app.py:18`, `nlp-service/api/services/core/transformers_engine.py:20-41` | Add `/health/ner-model/` endpoint. Log critical error and fail worker startup if model load returns `False` |
| 8 | MEDIUM | Prompt | Prompt sanitization strips ASCII markers but not Unicode homoglyphs or zero-width characters; bypass via fullwidth variants possible | `nlp-service/api/services/core/llm_engine.py:51-58` | Apply `unicodedata.normalize('NFKC', text)` before sanitization. Use delimited user-input blocks with explicit model instructions |
| 9 | MEDIUM | Async | `analyse` endpoint blocks with `await asyncio.to_thread` before returning 202 — connection may time out before response; 202 status is misleading | `nlp-service/api/routers/analyse.py:25` | Either remove `await` (truly fire-and-forget) or return 200 with the result synchronously |
| 10 | MEDIUM | Validation | No per-element validation on `pairs` list — a single-name pair or empty `sentences` passes through and wastes an LLM call | `nlp-service/api/routers/relations.py:27-29`, `PairSentences` model | Add `min_length=2, max_length=2` on `PairSentences.pair` and `min_length=1` on `PairSentences.sentences` |
| 11 | MEDIUM | Async | `find-pairs` endpoint has no rate limit; `run_in_executor` blocks threads on callback HTTP for up to 97s, risking ThreadPoolExecutor exhaustion under concurrent load | `nlp-service/api/routers/find_pairs.py:31` | Add `@limiter.limit("30/minute")` to the `find_pairs` router |
| 12 | MEDIUM | Tests | All 5 workflow functions have zero dedicated unit tests — exercised only indirectly via integration tests | `nlp-service/api/services/workflows/analyse_workflow.py`, `ner_workflow.py`, `find_pairs_workflow.py`, `relations_workflow.py`, `text_workflow.py` | Add dedicated unit tests for each workflow function, verifying callback invocation, error propagation, and output structure |
| 13 | LOW | Validation | `find_pairs` endpoint accepts empty `characters` dict silently — downstream `find_sentences_with_both_characters` returns `[]`, wasting resources | `nlp-service/api/routers/find_pairs.py:25-31`, `nlp-service/api/services/core/text_parser.py:11` | Return 422 when `characters` is empty or missing |
| 14 | LOW | Tokenizer | Token count falls back to `len(text) // 4` when `tiktoken` is absent — inaccurate for Polish (the frontend language); no warning emitted | `nlp-service/api/services/core/text_stats.py:31-34` | Use `len(text.split()) * 1.3` as fallback. Add `tokenizer: "heuristic"` field in response so consumers know the count is estimated |
| 15 | LOW | Tests | No test verifies callback delivery, LLM non-JSON response, or concurrent request behavior | Test gap analysis in Task 5 — `test_routes_*.py` mock `send_json` and `extract_entities_task.delay` | Add tests for callback HTTP failure, LLM non-JSON response, `asyncio.gather` partial failure, and tokenizer fallback without `tiktoken` |
| 16 | LOW | Config | `KAFKA_BOOTSTRAP_SERVERS` env var remains in `settings.py` despite Kafka removal in commit `22acdae` | `nlp-service/api/config/settings.py:49` | Remove `KAFKA_BOOTSTRAP_SERVERS` from `settings.py` |
| 17 | LOW | Code | `process_chapter_relations` is dead code — no HTTP endpoint calls this synchronous orchestration function | `nlp-service/api/services/workflows/relations_workflow.py` | Either add an HTTP endpoint or remove the dead code |

---

## Detailed Analysis

### Async Execution (Findings 1, 9, 5, 11)

Three of four business endpoints return HTTP 202 before any work is performed:

| Endpoint | File:Line | Mechanism | Task ID to client? | Failure reported? |
|----------|-----------|-----------|:---:|:---:|
| analyse | `analyse.py:25` | `await asyncio.to_thread` | No | Yes — exception propagates through `await` |
| ner | `ner.py:25` | `extract_entities_task.delay()` | Yes (Celery) | No — 202 returned before task runs |
| find-pairs | `find_pairs.py:31` | `run_in_executor` | No | No — only `add_done_callback` logs errors |
| relations | `relations.py:32` | `asyncio.create_task` | No | No — only `add_done_callback` logs errors |

The `analyse` endpoint is a special case: it uses `await`, which means the HTTP
handler **blocks** until `process_analyse` completes (including its callback).
This contradicts the 202 status code — the caller expects "processing continues
asynchronously" but receives "processing finished before the response." If the
work takes longer than the HTTP client timeout, the connection is dropped
despite successful server-side completion.

The `relations` endpoint has a compounding problem inside
`process_book_relations_async`. At `relations_workflow.py:111`, it uses:

```python
results = await asyncio.gather(*[extract_one(p) for p in pairs])
```

The default `return_exceptions=False` means a single LLM failure (e.g., timeout,
rate limit) raises an exception that cancels all remaining coroutines in the
batch. No callback is sent, no partial results are preserved — the client
received 202 and has no way to know zero relations were extracted.

The `find-pairs` endpoint uses `loop.run_in_executor(None, ...)` which defaults
to the global `ThreadPoolExecutor` (max_workers ≈ CPU cores + 4). Each
invocation of `process_find_pairs` calls `send_json` → `httpx.post`, blocking
a thread for up to 97 seconds (3 retries × ~30s timeout). Under concurrent load,
all threads can be occupied by HTTP callbacks rather than actual work.

### Callback Delivery (Findings 2)

All four endpoints send results to Django via `send_json()` in
`kafka/producer.py:37-43`. The function retries 3 times with exponential
backoff (1s → 2s → 4s, ~7 seconds total), then catches the final exception and
silently returns `None`:

```python
def send_json(topic: str, key: str, payload: dict) -> None:
    try:
        _post_callback(url, payload)
    except Exception:
        logger.exception("Callback to %s failed after retries", url)
        # return None implicitly
```

Every workflow function calls `send_json()` and ignores its return value:

| File | Line | Call |
|------|------|------|
| `analyse_workflow.py` | 22 | `send_json(TOPIC_ANALYSE_RESULTS, ...)` |
| `ner_workflow.py` | 23 | `send_json(TOPIC_NER_RESULTS, ...)` |
| `find_pairs_workflow.py` | 29 | `send_json(TOPIC_FIND_PAIRS_RESULTS, ...)` |
| `relations_workflow.py` | 114 | `send_json(TOPIC_RELATIONS_RESULTS, ...)` |

After `send_json` fails:
1. The exception is caught and logged (one log line).
2. The workflow returns its computed result — but fire-and-forget callers discard it.
3. The Django backend never receives the NLP output.
4. The client received HTTP 202 and cannot know data was lost.
5. No dead-letter queue, no retry queue, no local file — the result is gone permanently.

If Django is down for maintenance, all NLP results during that window are
silently lost with no replay mechanism. The expensive NLP computation
(NER, LLM extraction) was already performed before the callback is attempted.

### LLM Integration (Findings 3, 4, 8)

**Error swallowing (Finding 3).** `llm_engine.py:139-146` catches five OpenAI
exception types (`RateLimitError`, `APITimeoutError`, `APIConnectionError`,
`APIError`, plus `AuthenticationError`) and silently returns
`'{"relations": []}'`. The caller parses this JSON and treats it identically to
a successful extraction that found zero relationships. Rate limits, timeouts,
and connection failures are indistinguishable from "no relationship exists."

**Output validation absent (Finding 4).** Even when the LLM call succeeds,
the only validation is that the response parses as JSON. After parsing:

- Evidence strings are never checked against the input sentences — the model can hallucinate plausible-sounding quotes.
- Relation types are never validated against the allowed `RELATION_SCHEMA` values.
- Character names in the output are never checked against the requested pair.
- If `json.loads` raises `JSONDecodeError`, the output is stored as `{"raw": raw_string}` — which may contain markdown code fences (` ```json ... ``` `) that Django cannot interpret.

**Sanitization bypass (Finding 8).** `llm_engine.py:51-58` strips ASCII
markers (`SYSTEM:`, `ASSISTANT:`, `USER:`, ````, `---`, `###`) but does not
handle:
- Unicode fullwidth variants (e.g., `ＳＹＳＴＥＭ` using U+FF33)
- Zero-width joiners and non-printable Unicode characters
- Single `#` and `##` markdown headers (only `###` is stripped)
- Split markers reassembled by the model (`SYS` + `TEM:`)

### Validation Gaps (Findings 13, 10)

**Empty characters in find-pairs (Finding 13).** `find_pairs.py:29` uses
`(payload.characters or {}).keys()` which produces an empty list when
characters is `{}`, missing, or contains zero entries. The endpoint then calls
`process_find_pairs` with zero character names, producing no useful output.

**Per-element pair validation (Finding 10).** `relations.py:27-29` validates
that the `pairs` list is non-empty at the top level, but individual
`PairSentences` elements are not validated:

| Check | Validated? |
|-------|:----------:|
| `pairs` list non-empty | Yes |
| Each `pair` has exactly 2 names | No — `list[Name]` has no `min_length`/`max_length` |
| Each `pair` has non-empty `sentences` | No |
| Each sentence is within `max_length` | Via Pydantic `Sentence` model |

A pair with one character name or empty sentences passes validation and wastes
an LLM API call.

### Operational Health (Findings 6, 7, 14, 16, 17)

**Import-time side effects.** Three side effects occur at module import before
FastAPI starts:
1. `LLMService()` created in `llm_engine.py:183` — requires `OPENROUTER_API_KEY`.
2. `Celery()` created in `celery_app.py:10-12` — requires broker connectivity.
3. `load_ner_model` registered at `celery_app.py:16-18` via `@worker_process_init.connect`.

If `OPENROUTER_API_KEY` is unset or the broker is unreachable, the import fails
before FastAPI can serve any request — including health checks.

**NER model silent failure.** `transformers_engine.py:20-41` catches `OSError`
and `EnvironmentError` during model loading, returns `False`, and the caller
`extract_entities` returns `{}`. The Celery worker starts successfully, but
every NER task returns empty results posted to Django via callback. The
`/health/celery/` endpoint only checks broker connectivity, not model readiness.

**Dead code.** Two pieces of dead code persist:
- `KAFKA_BOOTSTRAP_SERVERS` env var in `settings.py:49` — Kafka was replaced
  with HTTP callbacks in commit `22acdae`, but the config variable remains.
- `process_chapter_relations` in `relations_workflow.py` — a synchronous
  orchestration function with no HTTP endpoint caller.

### Test Coverage (Findings 15, 12)

The test suite has 40 unit tests and 28 integration tests, all passing. However:

- All 5 workflow functions (`process_analyse`, `process_ner`,
  `process_find_pairs`, `process_chapter_relations`,
  `process_book_relations_async`) have **zero unit tests**. They are exercised
  only indirectly through integration tests that mock `send_json` and
  `extract_entities_task.delay`.

- Critical paths with no test coverage:
  - Callback HTTP failure (all integration tests mock `send_json`)
  - LLM non-JSON response (all LLM tests mock valid JSON output)
  - Concurrent fire-and-forget behavior (load testing)
  - NER model unavailable at runtime after worker startup
  - `asyncio.gather` exception cancellation with partial failures

---

## Remediation Priority

### P0 — Fix before production deployment

1. **Make background execution observable (Finding 1).** Return a job/request
   ID in every 202 response. Add `GET /jobs/{jobId}/status` that exposes
   Celery task state (`PENDING`/`STARTED`/`SUCCESS`/`FAILURE`) for `ner`, and
   track executor/coroutine status in an in-memory store (or Redis) for
   `find-pairs` and `relations`.

2. **Surface callback failures (Finding 2).** Use Celery tasks for all
   callbacks — this gives persistent storage, automatic retry with exponential
   backoff, and `CELERY_RESULT_BACKEND` tracking. At minimum, write failed
   callbacks to a dead-letter log file as JSON Lines for manual replay.

3. **Return error metadata on LLM failures (Finding 3).** Return distinguishable
   error values (e.g., `'{"error": "rate_limit"}'`) instead of empty relations.
   Propagate error metadata through the callback so Django can record per-pair
   failure status.

4. **Validate LLM JSON output (Finding 4).** After JSON parse: validate that
   `evidence` strings are substrings of the input sentences, `relation` values
   are in `RELATION_SCHEMA`, and character names match the requested pair.
   Add a `json_parse_error` flag to results so Django can distinguish real data
   from fallback.

5. **Fix `asyncio.gather` exception handling (Finding 5).** Use
   `asyncio.gather(..., return_exceptions=True)` in
   `relations_workflow.py:111` so partial results are collected even when
   individual pair extraction fails. Process results vs. exceptions and send
   what succeeded via callback.

### P1 — Fix within next sprint

6. **Defer LLMService instantiation (Finding 6).** Convert to lazy singleton
   via `@lru_cache` factory or FastAPI `on_startup` hook so import errors do not
   block health checks.

7. **Add NER model health check (Finding 7).** Add a `/health/ner-model/`
   endpoint that verifies `_NER_PIPELINES[DEFAULT_NER_MODEL]` is populated.
   Log a critical error and fail worker startup if `load_ner_model` returns
   `False`.

8. **Fix `analyse` endpoint blocking (Finding 9).** Either remove `await`
   (truly fire-and-forget, consistent with other endpoints) or change the
   response to 200 with the result synchronously. Do not mix 202 with blocking
   behavior.

9. **Add per-element validation on pairs (Finding 10).** Add
   `min_length=2, max_length=2` on `PairSentences.pair` and `min_length=1`
   on `PairSentences.sentences` in the Pydantic model, or validate in the
   router before dispatching.

10. **Unicode-safe prompt sanitization (Finding 8).** Apply
    `unicodedata.normalize('NFKC', text)` before sanitization to collapse
    fullwidth and compatibility characters. Consider using a dedicated
    prompt-injection detection approach (e.g., delimited user-input blocks
    with explicit model instructions).

11. **Rate-limit find-pairs endpoint (Finding 11).** Add
    `@limiter.limit("30/minute")` to the `find_pairs` router to prevent thread
    pool exhaustion under load.

### P2 — Nice to have

12. **Reject empty characters in find-pairs (Finding 13).** Return 422 when
    `characters` is empty or missing, rather than silently processing with
    zero character names.

13. **Language-aware token fallback (Finding 14).** Use `len(text.split()) * 1.3`
    as fallback (word-based heuristic) instead of `len(text) // 4`. At minimum,
    include a `tokenizer: "heuristic"` field in the response so consumers know
    the count is estimated.

14. **Integration tests for callback and LLM edge cases (Finding 15).** Add tests
    for: callback HTTP failure (mock `httpx.post` to raise `ConnectError`), LLM
    non-JSON response (` ```json\n{...}\n``` `), `asyncio.gather` partial
    failure, and tokenizer fallback without `tiktoken`.

15. **Unit tests for workflow functions (Finding 12).** Add dedicated unit tests
    for each of the 5 workflow functions, verifying callback invocation, error
    propagation, and output structure independently from HTTP routing.

16. **Remove Kafka dead code (Finding 16).** Remove `KAFKA_BOOTSTRAP_SERVERS`
    from `settings.py`.

17. **Wire up or remove `process_chapter_relations` (Finding 17).** Either add
    an HTTP endpoint that uses this function or remove the dead code.

---

## Residual Risk

After implementing P0 fixes, the service remains dependent on:

- **Django callback endpoint availability.** No circuit breaker or health-based
  routing — if Django is unreachable, all NLP results are lost (mitigated by
  Celery callback retry after P0.2, but persistent unavailability still causes
  eventual data loss).
- **Celery broker and backend.** Single point of failure for NER tasks and
  (after remediation) all callbacks. Redis downtime blocks all NER processing.
- **OpenRouter API availability.** No offline cache or fallback model for
  relation extraction. LLM unavailability returns empty relations for all
  character pairs.
- **No async timeouts on any endpoint.** `celery_app.py` has no
  `CELERY_TASK_SOFT_TIME_LIMIT`/`CELERY_TASK_TIME_LIMIT` configured.
  `asyncio.create_task` and `run_in_executor` have no timeout wrapping.
  A hung thread or coroutine is never cancelled.
- **Import-time fragility remains** until P1.6 is implemented.
  `OPENROUTER_API_KEY` must be set before import or the entire service crashes
  at startup.

These are integration dependencies outside the NLP service scope. Monitor them
with healthcheck probes in the orchestration layer. Consider adding a
`/health/django-reachable/` endpoint that tests callback connectivity and
degrades the NLP service health status if Django is unreachable.

---

## Verification Results (2026-05-11)

| Check | Result |
|-------|--------|
| Unit tests (40 tests) | All passed (6.80s) |
| Integration tests (28 tests) | All passed (31.43s) |
| Import-time startup | No errors — title "StoryWeave API" |
| Route inventory | 11 routes (4 business + 7 infrastructure) |
| Env variable wiring | `OPENROUTER_API_KEY` loaded at import; LLM client initialized |
| Payload field access vs. models | 0 mismatches — all 12 field accesses match Pydantic definitions |
| Response model declarations | All 4 endpoints declare `response_model=AcceptedResponse`, `status_code=202` |
| Rate limiting | `relations` (30/min), `ner` (30/min), `analyse` and `find-pairs` have no limits |

---

## Summary

| Severity | Count |
|----------|:-----:|
| HIGH | 5 |
| MEDIUM | 7 |
| LOW | 5 |
| **Total** | **17** |

**Overall assessment: DONE_WITH_CONCERNS.** The service has known gaps in
observability, callback reliability, and LLM output validation. All existing
tests pass, but critical failure paths (callback delivery, LLM non-JSON
response, concurrent load) are untested. The service is functional for
development use but requires P0 remediation before production deployment.
