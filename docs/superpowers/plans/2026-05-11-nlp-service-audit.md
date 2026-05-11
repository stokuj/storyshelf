# NLP Service Full Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Perform a full audit of `nlp-service` only, verify the main runtime paths with tests and runtime checks, and produce a prioritized audit report with concrete remediation items.

**Architecture:** Audit the service in layers: first map the entry points and configuration, then validate each request path through routers, workflows, tasks, and callback code, then measure the test gaps and operational risks, and finally write a single report with findings sorted by severity. Keep the audit isolated to `nlp-service` so the output stays focused and actionable.

**Tech Stack:** FastAPI, Celery, pytest, Python 3.13, httpx, transformers, OpenAI SDK, SlowAPI

---

**Attention Conservation Notice**
For: Engineers auditing `nlp-service`
What: Full service audit plan for the NLP microservice only
Action: Follow the steps in order and write findings into the final report
Skip if: You are not responsible for NLP service quality or production risk

## Before You Start

Work from the repo root, but keep every check scoped to `nlp-service/` unless a callback path or integration point requires a read-only reference in Django.

Use `DJANGO_ENV` only when a check explicitly touches the callback target or shared monorepo behavior. Do not expand the audit into unrelated backend or frontend work.

## Output

The final deliverable is an audit report at `docs/superpowers/reports/2026-05-11-nlp-service-audit.md`.

During audit, capture raw findings in a working notepad at `docs/superpowers/reports/2026-05-11-nlp-service-audit-notes.md` so no observation is lost between tasks. Commit this file after every task.

The final report contains:
- a short executive summary
- a severity-ranked findings table
- evidence for each finding (file:line + reproduction command or test output)
- concrete remediation recommendations
- a short note on residual risk after the audit

---

### Task 1: Map the service surface area

**Files:**
- Read: `nlp-service/README.md`
- Read: `nlp-service/pyproject.toml`
- Read: `nlp-service/api/app.py`
- Read: `nlp-service/api/config/settings.py`
- Read: `nlp-service/api/config/celery_app.py`
- Read: `nlp-service/api/models/model.py`
- Read: `nlp-service/api/kafka/producer.py`
- Create: `docs/superpowers/reports/2026-05-11-nlp-service-audit-notes.md`

- [ ] **Step 1: Dump every registered route path to the notes file**

Run: `cd nlp-service && uv run python -c "
from api.app import app
for route in sorted(app.routes, key=lambda r: r.path):
    methods = ','.join(route.methods) if hasattr(route, 'methods') else ''
    print(f'{methods:8s} {route.path}')
" >> ../docs/superpowers/reports/2026-05-11-nlp-service-audit-notes.md`

Expected: All 5+ route paths listed.

- [ ] **Step 2: Record runtime architecture (request path per feature)**

Append to `notes.md` a table:

```markdown
| Feature    | Entry route                | Router file            | Workflow function           | Task / background       | Callback topic        |
|------------|----------------------------|------------------------|-----------------------------|-------------------------|-----------------------|
| analyse    | POST /chapters/{id}/analyse | routers/analyse.py    | process_analyse             | asyncio.to_thread       | chapter.analyse.results |
| ner        | POST /chapters/{id}/ner     | routers/ner.py        | process_ner                 | Celery task             | chapter.ner.results    |
| find-pairs | POST /books/{id}/find-pairs | routers/find_pairs.py | process_find_pairs          | run_in_executor         | book.find-pairs.results|
| relations  | POST /books/{id}/relations  | routers/relations.py  | process_book_relations_async| asyncio.create_task     | book.relations.results |
```

- [ ] **Step 3: Audit import-time side effects with a targeted scan**

Run: `cd nlp-service && uv run python -c "
import os
os.environ.setdefault('OPENROUTER_API_KEY', 'audit-fake-key')
from api.services.core.llm_engine import llm_service
print('LLMService instantiated at import:', type(llm_service).__name__)
print('async_client:', type(llm_service._async_client).__name__)
print('sync_client:', type(llm_service._sync_client).__name__)
from api.config.celery_app import celery
print('Celery app:', celery.main)
print('Broker:', celery.conf.broker_url)
"`

Expected: Three side effects identified: `LLMService()` at module level, `Celery()` at module level, `load_ner_model` at `worker_process_init`.

- [ ] **Step 4: Dump environment variable baseline**

Run: `grep -no 'os\.getenv\|os\.environ' nlp-service/api/config/settings.py nlp-service/api/app.py nlp-service/api/services/core/llm_engine.py nlp-service/api/services/core/transformers_engine.py nlp-service/api/kafka/producer.py >> docs/superpowers/reports/2026-05-11-nlp-service-audit-notes.md`

Expected: All env-var reads listed with file:line.

- [ ] **Step 5: Commit the audit notepad**

```bash
git add docs/superpowers/reports/2026-05-11-nlp-service-audit-notes.md
git commit -m "audit(nlp): task 1 — surface area map, route inventory, side effects baseline"
```

---

### Task 2: Audit request validation and API behavior

**Files:**
- Read: `nlp-service/api/routers/analyse.py`
- Read: `nlp-service/api/routers/ner.py`
- Read: `nlp-service/api/routers/find_pairs.py`
- Read: `nlp-service/api/routers/relations.py`
- Read: `nlp-service/api/models/model.py`
- Read: `nlp-service/api/app.py`
- Modify: `docs/superpowers/reports/2026-05-11-nlp-service-audit-notes.md`

- [ ] **Step 1: Diff each endpoint's payload model against its router validation**

For each of the four endpoints, run:

```bash
grep -n 'payload\.' nlp-service/api/routers/analyse.py
grep -n 'payload\.' nlp-service/api/routers/ner.py
grep -n 'payload\.' nlp-service/api/routers/find_pairs.py
grep -n 'payload\.' nlp-service/api/routers/relations.py
```

Then check every `payload.field` access against the fields defined in `nlp-service/api/models/model.py`. Append to notes any field mismatch or missing validation.

- [ ] **Step 2: Check response model declarations**

Run:

```bash
grep -no 'response_model\|status_code' nlp-service/api/routers/analyse.py nlp-service/api/routers/ner.py nlp-service/api/routers/find_pairs.py nlp-service/api/routers/relations.py >> docs/superpowers/reports/2026-05-11-nlp-service-audit-notes.md
```

Verify that every endpoint returning `202` uses `AcceptedResponse` and that no endpoint reports success before verifying the background work actually started.

- [ ] **Step 3: Inspect rate limiting placement**

Run:

```bash
grep -no '@limiter\.limit\|Limiter' nlp-service/api/routers/relations.py nlp-service/api/routers/ner.py nlp-service/api/routers/analyse.py nlp-service/api/routers/find_pairs.py
```

Expected: Only `ner` and `relations` are rate-limited. If other endpoints lack limits, note it.

- [ ] **Step 4: Identify validation gaps in edge cases**

Read `nlp-service/api/routers/find_pairs.py:24-27` and `nlp-service/api/routers/relations.py:25-29`. Notice that:

- `find_pairs` rejects empty `content` but accepts empty `characters` silently.
- `relations` rejects empty `pairs` but does not validate individual `pair` elements (e.g., a pair with one element, or empty sentences).

Append these observations to the notes file.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/reports/2026-05-11-nlp-service-audit-notes.md
git commit -m "audit(nlp): task 2 — endpoint contract validation, response models, rate limits"
```

---

### Task 3: Audit core NLP workflows and helper code

**Files:**
- Read: `nlp-service/api/services/workflows/analyse_workflow.py`
- Read: `nlp-service/api/services/workflows/ner_workflow.py`
- Read: `nlp-service/api/services/workflows/find_pairs_workflow.py`
- Read: `nlp-service/api/services/workflows/relations_workflow.py`
- Read: `nlp-service/api/services/core/text_stats.py`
- Read: `nlp-service/api/services/core/text_parser.py`
- Read: `nlp-service/api/services/core/transformers_engine.py`
- Read: `nlp-service/api/services/core/llm_engine.py`
- Modify: `docs/superpowers/reports/2026-05-11-nlp-service-audit-notes.md`

- [ ] **Step 1: Trace each workflow's success and failure return values**

Run this script and redirect output to notes:

```bash
cd nlp-service && uv run python -c "
import inspect, json
from api.services.workflows.analyse_workflow import process_analyse
from api.services.workflows.ner_workflow import process_ner
from api.services.workflows.find_pairs_workflow import process_find_pairs
from api.services.workflows.relations_workflow import process_book_relations_async, process_chapter_relations

for name, fn in [('process_analyse', process_analyse), ('process_ner', process_ner),
                  ('process_find_pairs', process_find_pairs), ('process_chapter_relations', process_chapter_relations),
                  ('process_book_relations_async', process_book_relations_async)]:
    sig = inspect.signature(fn)
    params = {k: str(v.annotation) for k, v in sig.parameters.items()}
    ret = sig.return_annotation
    print(f'{name}({json.dumps(params)}) -> {ret}')
    print(f'  docstring: {inspect.getdoc(fn)[:120] if inspect.getdoc(fn) else \"(none)\"}')
    print()
" >> docs/superpowers/reports/2026-05-11-nlp-service-audit-notes.md
```

- [ ] **Step 2: Audit error fallback in LLM and callback code**

Read `nlp-service/api/services/core/llm_engine.py:139-146` and `nlp-service/api/kafka/producer.py:37-43`. Note in the audit notes:

- **LLM**: five OpenAI exception types swallowed silently — callers never know extraction failed. Data loss is silent.
- **Callback**: `send_json` retries 3 times with exponential backoff, then logs exception and returns `None`. Workflow functions call `send_json` for side effect only — they return their result regardless of callback success.

- [ ] **Step 3: Check model loading and tokenizer fallbacks**

Read `nlp-service/api/services/core/transformers_engine.py:20-41` and `nlp-service/api/services/core/text_stats.py:16-34`. Append to notes:

- **NER model**: cached in `_NER_PIPELINES` dict. If model not available, returns `False` and `extract_entities` returns `{}` — no error raised upstream.
- **Tokenizer**: `tiktoken` is optional. If missing, falls back to `len(text) // 4`. The comment at `nlp-service/api/services/core/text_stats.py:32` says this is a heuristic — it is inaccurate for non-English text.

- [ ] **Step 4: Evaluate LLM prompt for injection and correctness**

Read `nlp-service/api/services/core/llm_engine.py:60-103`. Append to notes:

- **Sanitization**: `_sanitize` removes ````", "---", "###", "SYSTEM:", "ASSISTANT:", "USER:"` markers and ASCII control chars. Acceptable but not watertight (does not strip Unicode variants like `ＳＹＳＴＥＭ` fullwidth).
- **Prompt contract**: Instructs the model to return ONLY JSON. The wrapper uses `json.loads` — if the model hallucinates extra text, it falls back to `{"raw": raw_string}` (`relations_workflow.py:82`), which the Django callback may not handle.
- **Evidence quality**: Prompt requires direct quotes as evidence. No guarantee the model complies — and no post-processing validates that evidence actually appears in the input sentences.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/reports/2026-05-11-nlp-service-audit-notes.md
git commit -m "audit(nlp): task 3 — workflow trace, LLM fallback risks, model loading audit"
```

---

### Task 4: Audit async execution, Celery, and callback delivery

**Files:**
- Read: `nlp-service/api/tasks/ner_task.py`
- Read: `nlp-service/api/tasks/find_pairs_task.py`
- Read: `nlp-service/api/config/celery_app.py`
- Read: `nlp-service/api/kafka/producer.py`
- Read: `nlp-service/api/services/workflows/relations_workflow.py`
- Modify: `docs/superpowers/reports/2026-05-11-nlp-service-audit-notes.md`

- [ ] **Step 1: Verify Celery task registration and worker init**

Run:

```bash
grep -n 'celery\.task\|@celery\.task\|@worker_process_init\|load_ner_model\|include\|broker\|backend' nlp-service/api/config/celery_app.py nlp-service/api/tasks/ner_task.py nlp-service/api/tasks/find_pairs_task.py >> docs/superpowers/reports/2026-05-11-nlp-service-audit-notes.md
```

Check: `celery_app.py:12` includes only `ner_task` and `find_pairs_task`. `worker_process_init` loads the NER model at worker startup — if the model is unavailable, the worker starts but tasks fail later. Append this observation to notes.

- [ ] **Step 2: Audit fire-and-forget execution in each router**

Run:

```bash
grep -n 'asyncio\.to_thread\|run_in_executor\|asyncio\.create_task\|\.delay(' nlp-service/api/routers/analyse.py nlp-service/api/routers/ner.py nlp-service/api/routers/find_pairs.py nlp-service/api/routers/relations.py
```

Expected matches:

| File | Line | Mechanism | Task ID returned? | Failure reported? |
|------|------|-----------|-------------------|-------------------|
| `analyse.py` | 25 | `asyncio.to_thread` | No | Only via `log_requests` middleware (4xx/5xx and exceptions) |
| `ner.py` | 25 | `extract_entities_task.delay()` | Yes (Celery task ID) | Celery worker logs only |
| `find_pairs.py` | 31 | `run_in_executor` | No | `add_done_callback` logs error only |
| `relations.py` | 32 | `asyncio.create_task` | No | `add_done_callback` logs error only |

Append this table to notes as a finding: three out of four endpoints are **unobservable fire-and-forget**.

- [ ] **Step 3: Check callback retries and failure propagation**

Read `nlp-service/api/kafka/producer.py:24-43`. Trace the failure path:

```
send_json() calls _post_callback() → httpx.post() → 3 retries with 2**attempt backoff
→ if all retries fail, raise → caught by send_json() except → log.exception() → return None
```

Workflow functions (`process_find_pairs:29`, `process_ner:23`, etc.) call `send_json()` and ignore its return value. Append finding: **callback failure is logged but never surfaced to the caller or the original HTTP response**.

- [ ] **Step 4: Identify async/sync boundary risks**

Read `nlp-service/api/routers/find_pairs.py:31`. The `run_in_executor(None, process_find_pairs, ...)` call uses the default `ThreadPoolExecutor`. `process_find_pairs` calls `send_json` which calls `httpx.post` (synchronous). This is safe in a thread but ties up the thread pool. If many concurrent requests pile up, they compete for the default small thread pool.

Read `nlp-service/api/routers/relations.py:32`. `asyncio.create_task` schedules the coroutine on the event loop. If `process_book_relations_async` raises an unhandled exception inside `asyncio.gather`, the callback catches it only in `_log_task_result`. The HTTP response still returns `202 Accepted` — the caller never knows the work failed.

Append both observations to notes.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/reports/2026-05-11-nlp-service-audit-notes.md
git commit -m "audit(nlp): task 4 — async execution audit, fire-and-forget, callback failures"
```

---

### Task 5: Measure test coverage and gap risk

**Files:**
- Read: `nlp-service/test/conftest.py`
- Read: `nlp-service/test/unit/test_book_service.py`
- Read: `nlp-service/test/unit/test_transformers_service.py`
- Read: `nlp-service/test/unit/test_llm_service.py`
- Read: `nlp-service/test/integration/test_routes_app.py`
- Read: `nlp-service/test/integration/test_routes_analyse.py`
- Read: `nlp-service/test/integration/test_routes_ner.py`
- Read: `nlp-service/test/integration/test_routes_find_pairs.py`
- Read: `nlp-service/test/integration/test_routes_relations.py`
- Read: `nlp-service/test/integration/test_rate_limits.py`
- Modify: `docs/superpowers/reports/2026-05-11-nlp-service-audit-notes.md`

- [ ] **Step 1: Map unit test coverage to actual code paths**

Run a targeted scan of what each unit test actually exercises:

```bash
cd nlp-service && uv run python -c "
import ast, sys

test_files = [
    'test/unit/test_book_service.py',
    'test/unit/test_transformers_service.py',
    'test/unit/test_llm_service.py',
]

for tf in test_files:
    tree = ast.parse(open(tf).read())
    classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    functions = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]
    print(f'{tf}:')
    for cls in classes:
        print(f'  class {cls}')
    for fn in functions:
        print(f'    test: {fn}')
    print()
" >> docs/superpowers/reports/2026-05-11-nlp-service-audit-notes.md
```

Then append a gap summary to notes:

```markdown
## Test coverage gaps

| Test file | Code paths covered | Code paths NOT covered |
|-----------|-------------------|----------------------|
| test_book_service.py | text_stats.analyse_text, text_parser.find_sentences_with_both_characters | tokenizer fallback when tiktoken missing, sentence regex edge cases |
| test_transformers_service.py | load_ner_model, extract_entities (unit) | actual model inference, concurrency, worker init at startup |
| test_llm_service.py | extract_relations (async), error fallback for 5 exception types | extract_relations_sync, prompt injection, json.loads fallback |
| test_routes_app.py | root, /health/, /health/celery/, 500 handler | graceful shutdown, real Celery connection failure |
| test_routes_analyse.py | 202 on valid, 422 on missing/whitespace content | callback delivery, async exceptions |
| test_routes_ner.py | 202 on valid, 422 on missing/whitespace content | Celery task execution, callback delivery |
| test_routes_find_pairs.py | 202 on valid, 422 on missing/whitespace content, empty characters accepted | run_in_executor exceptions, callback delivery |
| test_routes_relations.py | 202 on valid, 422 on mismatched IDs, 422 on empty pairs | async.coroutine failures, callback delivery, invalid pair element |
| test_rate_limits.py | 429 after 30 requests on ner and relations | rate limit on other endpoints, key rotation |
```

- [ ] **Step 2: Identify critical untested behaviors**

Append to notes a specific list of **untested production risks**:

```markdown
## Critical untested behaviors

1. **Callback HTTP failure** — no test verifies what happens when `CALLBACK_BASE_URL` is unreachable.
2. **LLM returns non-JSON** — no test verifies the `json.JSONDecodeError → {"raw": ...}` fallback in `relations_workflow.py:82`.
3. **NER model unavailable at runtime** — only tested in unit; integration test always mocks the pipeline.
4. **Concurrent fire-and-forget** — no test verifies behavior under load (e.g., 50 concurrent `find_pairs` requests share the same thread pool).
5. **Worker restart with stale state** — no test verifies `_NER_PIPELINES` is cleared on worker restart.
6. **Token counting without tiktoken** — fallback `len(text) // 4` is tested only indirectly (tiktoken is always installed in CI).
```

- [ ] **Step 3: Validate test isolation**

Run:

```bash
grep -n 'OPENROUTER_API_KEY\|os\.environ\|setdefault\|_NER_PIPELINES\|autouse\|clear_pipelines' nlp-service/test/conftest.py nlp-service/test/unit/test_transformers_service.py >> docs/superpowers/reports/2026-05-11-nlp-service-audit-notes.md
```

Confirm findings:
- `conftest.py:5` — `OPENROUTER_API_KEY` setdefault before any import.
- `test_transformers_service.py:9` — `clear_pipelines` autouse fixture resets `_NER_PIPELINES`.
- No other test module uses `autouse` — other tests may leak global state.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/reports/2026-05-11-nlp-service-audit-notes.md
git commit -m "audit(nlp): task 5 — test coverage map, gap analysis, isolation audit"
```

---

### Task 6: Run focused verification checks

**Files:**
- Read: `nlp-service/pyproject.toml`
- Read: `nlp-service/test/**/*.py`
- Modify: `docs/superpowers/reports/2026-05-11-nlp-service-audit-notes.md`

- [ ] **Step 1: Run the unit test suite**

```bash
cd nlp-service && uv run pytest test/unit -v 2>&1 | tee -a ../docs/superpowers/reports/2026-05-11-nlp-service-audit-notes.md
```

Expected: All tests pass. If any test fails, document the failure as a finding.

- [ ] **Step 2: Run the integration test suite**

```bash
cd nlp-service && uv run pytest test/integration/test_routes_app.py test/integration/test_routes_analyse.py test/integration/test_routes_ner.py test/integration/test_routes_find_pairs.py test/integration/test_routes_relations.py test/integration/test_rate_limits.py -v 2>&1 | tee -a ../docs/superpowers/reports/2026-05-11-nlp-service-audit-notes.md
```

Expected: Integration tests pass. Any failure is a finding.

- [ ] **Step 3: Verify import-time startup does not fail**

```bash
cd nlp-service && uv run python -c "
from api.app import app
print('title:', app.title)
print('routes:', len(app.routes))
" 2>&1 | tee -a ../docs/superpowers/reports/2026-05-11-nlp-service-audit-notes.md
```

Expected: `title: StoryWeave API`, routes count > 5, no import error.

- [ ] **Step 4: Verify module-level env reads**

```bash
cd nlp-service && OPENROUTER_API_KEY=audit-key uv run python -c "
from api.services.core.llm_engine import llm_service
assert llm_service._async_client.api_key == 'audit-key', f'Expected audit-key, got {llm_service._async_client.api_key}'
print('LLM client initialized with provided key')
" 2>&1 | tee -a ../docs/superpowers/reports/2026-05-11-nlp-service-audit-notes.md
```

Expected: Confirmation that the key is read at import time.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/reports/2026-05-11-nlp-service-audit-notes.md
git commit -m "audit(nlp): task 6 — test run results, startup check, env verification"
```

---

### Task 7: Write the audit report

**Files:**
- Read: `docs/superpowers/reports/2026-05-11-nlp-service-audit-notes.md`
- Create: `docs/superpowers/reports/2026-05-11-nlp-service-audit.md`

- [ ] **Step 1: Write the executive summary**

Create the report file and write a 3-4 sentence summary of the service's overall health: what it does, the biggest risk found, and whether it's production-safe.

```markdown
# NLP Service Audit Report — 2026-05-11

## Executive Summary

The NLP service (`storyweave` v0.9.1) provides four endpoints for text analysis,
NER, character-pair discovery, and LLM-powered relation extraction. It handles
asynchronous work through Celery tasks and fire-and-forget background jobs, and
reports results back to Django via HTTP callbacks.

The principal risk is **silent data loss**: three of four endpoints use
unobservable fire-and-forget execution, and callback failures are swallowed
without surfacing to callers. Import-time side effects make the service fragile
at startup and in tests.

The service is **not production-safe** in its current state. Remediation
requires making background execution observable and hardening the callback path.

---

## Findings
```

- [ ] **Step 2: Build the findings table from notes**

Extract every observation from `audit-notes.md` into a table with these columns:

```markdown
| # | Severity | Area | Description | Evidence | Recommendation |
|---|----------|------|-------------|----------|----------------|
| 1 | HIGH | Async | Fire-and-forget execution in 3/4 endpoints — caller receives 202 before work is verified | `routers/find_pairs.py:31`, `routers/relations.py:32`, `routers/analyse.py:25` | Return a task/request ID and expose a status endpoint (polling or webhook). |
| 2 | HIGH | Callback | `send_json` swallows HTTP callback failures — Django never learns of completed work | `kafka/producer.py:37-43` | Surface callback failure in the original HTTP response or emit to a dead-letter queue. |
| 3 | HIGH | LLM | `LLMService` hungrily swallows 5 OpenAI exception types — caller receives empty relations without knowing extraction failed | `llm_engine.py:139-146`, `llm_engine.py:173-180` | Return error metadata alongside empty relations or raise a domain exception. |
| 4 | MEDIUM | Startup | `LLMService()` instantiated at module import — any env misconfiguration breaks imports before FastAPI starts | `llm_engine.py:183` | Defer client creation to a `@lru_cache` factory or `on_startup` hook. |
| 5 | MEDIUM | NER | NER model loaded at Celery worker init — if model download fails, workers start but every NER task returns `{}` | `celery_app.py:18`, `transformers_engine.py:20-41` | Add a startup health check probe that verifies the model loaded. |
| 6 | MEDIUM | Validation | `find_pairs` endpoint accepts empty `characters` dict silently — downstream `find_sentences_with_both_characters` returns `[]` | `routers/find_pairs.py:25-31`, `text_parser.py:11` | Reject empty `characters` at the router level or explicitly handle it in the workflow. |
| 7 | LOW | Tokenizer | Token count falls back to `len(text) // 4` when `tiktoken` is absent — inaccurate for Polish (the frontend language) | `text_stats.py:29-34` | Make `tiktoken` a required dependency or use a language-aware fallback (e.g., `len(text.split()) * 1.3`). |
| 8 | LOW | Tests | No test verifies callback delivery, LLM non-JSON response, or concurrent request behavior | test gap analysis in Task 5 | Add integration tests for the callback path and LLM response edge cases. |
| 9 | LOW | Prompt | Prompt sanitization strips ASCII markers but not Unicode lookalike characters | `llm_engine.py:51-58` | Use `unicodedata.normalize('NFKC', text)` before sanitization. |
```

- [ ] **Step 3: Write the remediation order**

Group findings into priority buckets:

```markdown
## Remediation Priority

### P0 — Fix before production deployment
1. Make background execution observable (Finding #1)
2. Surface callback failures to callers (Finding #2)
3. Return error metadata on LLM failures (Finding #3)

### P1 — Fix within next sprint
4. Defer LLMService instantiation to startup (Finding #4)
5. Add NER model health check (Finding #5)
6. Reject empty characters in find-pairs (Finding #6)

### P2 — Nice to have
7. Language-aware token fallback (Finding #7)
8. Integration tests for callback and LLM edge cases (Finding #8)
9. Unicode-safe prompt sanitization (Finding #9)
```

- [ ] **Step 4: Add residual risk note**

```markdown
## Residual Risk

After implementing P0 fixes, the service remains dependent on:
- Django callback endpoint availability (no circuit breaker)
- Celery broker and backend (single point of failure for NER)
- OpenRouter API availability (no offline cache or fallback model)

These are integration dependencies outside the NLP service scope. Monitor them
with healthcheck probes in the orchestration layer.
```

- [ ] **Step 5: Commit the final report**

```bash
git add docs/superpowers/reports/2026-05-11-nlp-service-audit.md
git rm docs/superpowers/reports/2026-05-11-nlp-service-audit-notes.md
git commit -m "audit(nlp): task 7 — final audit report with findings, remediation, residual risk"
```

---

### Task 8: Self-review and handoff

**Files:**
- Read: `docs/superpowers/reports/2026-05-11-nlp-service-audit.md`

- [ ] **Step 1: Scan for vague findings without evidence**

Run:

```bash
grep -n 'file:line\|Evidence' docs/superpowers/reports/2026-05-11-nlp-service-audit.md
```

Every finding in the table must have a `file.py:line` reference or a reproduction command. If any row lacks evidence, either add it or remove the finding.

- [ ] **Step 2: Check severity ordering**

Verify that HIGH findings appear first, then MEDIUM, then LOW. Reorder rows if needed.

- [ ] **Step 3: Confirm scope boundary**

Run:

```bash
grep -o 'django\|frontend\|backend-django' docs/superpowers/reports/2026-05-11-nlp-service-audit.md | sort | uniq -c
```

If Django is mentioned more than in passing (Residual Risk section and callback references are fine), trim to keep the report `nlp-service`-only.

- [ ] **Step 4: Commit the completed report**

```bash
git add docs/superpowers/reports/2026-05-11-nlp-service-audit.md
git commit -m "audit(nlp): finalize report after self-review"
```

- [ ] **Step 5: Handoff**

Print the summary:

```
Audit complete. Report saved at docs/superpowers/reports/2026-05-11-nlp-service-audit.md

Key findings:
- 3 HIGH severity issues (fire-and-forget execution, silent callback failure, LLM error swallowing)
- 3 MEDIUM severity issues (import-time side effects, NER model startup, empty characters)
- 3 LOW severity issues (tokenizer fallback, test gaps, prompt sanitization)

P0 fixes required before production deployment. See the report for full details.
```
