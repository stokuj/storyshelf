# NLP Service Audit — Task 1: Surface Area Map
# Date: 2026-05-11

## Step 1 — Registered Route Inventory

```
GET      /
POST     /books/{bookId}/find-pairs
POST     /books/{bookId}/relations
POST     /chapters/{chapterId}/analyse
POST     /chapters/{chapterId}/ner
GET,HEAD /docs
GET,HEAD /docs/oauth2-redirect
GET      /health/
GET      /health/celery/
GET,HEAD /openapi.json
GET,HEAD /redoc
```

11 routes total. 4 business endpoints (analyse, ner, find-pairs, relations), 1 root, 2 health checks, 4 FastAPI built-ins (docs, openapi.json, redoc, oauth2-redirect).

## Step 2 — Runtime Architecture (request path per feature)

| Feature    | Entry route                  | Router file            | Workflow function             | Task / background       | Callback topic           |
|------------|------------------------------|------------------------|-------------------------------|-------------------------|--------------------------|
| analyse    | POST /chapters/{id}/analyse  | routers/analyse.py    | process_analyse               | asyncio.to_thread       | chapter.analyse.results  |
| ner        | POST /chapters/{id}/ner      | routers/ner.py        | extract_entities_task.delay() | Celery task             | chapter.ner.results      |
| find-pairs | POST /books/{id}/find-pairs  | routers/find_pairs.py | process_find_pairs            | run_in_executor         | book.find-pairs.results  |
| relations  | POST /books/{id}/relations   | routers/relations.py  | process_book_relations_async  | asyncio.create_task     | book.relations.results   |

All callbacks go via HTTP POST to Django internal endpoints through `api/kafka/producer.py` → `send_json()`.

## Step 3 — Import-Time Side Effects

Three side effects identified:

1. **`LLMService()` at module level** — `api/services/core/llm_engine.py` instantiates `LLMService()` at import time, creating async and sync OpenAI clients before any request is served. Requires `OPENROUTER_API_KEY` to be set in the environment before import.
2. **`Celery()` at module level** — `api/config/celery_app.py` instantiates `Celery("app", ...)` at import time, connecting to the broker URL from settings.
3. **`load_ner_model` at `worker_process_init`** — `api/config/celery_app.py` registers a `@worker_process_init.connect` signal handler that calls `load_ner_model(DEFAULT_NER_MODEL)`, loading the transformer model into memory when each Celery worker process starts.

### Scan output

```
LLMService instantiated at import: LLMService
async_client: AsyncOpenAI
sync_client: OpenAI
Celery app: app
Broker: redis://localhost:6379/0
```

## Step 4 — Environment Variable Baseline

All `os.getenv` / `os.environ` reads across the service:

```
nlp-service/api/config/settings.py:14:_env = os.getenv("APP_ENV", "development").lower()
nlp-service/api/config/settings.py:17:    CORS_ALLOW_ORIGINS: list[str] = os.getenv("CORS_ALLOW_ORIGINS", "").split(",")
nlp-service/api/config/settings.py:23:    CORS_ALLOW_ORIGINS: list[str] = os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
nlp-service/api/config/settings.py:25:        os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
nlp-service/api/config/settings.py:31:CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
nlp-service/api/config/settings.py:32:CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
nlp-service/api/config/settings.py:35:OPENROUTER_API_KEY: str | None = os.getenv("OPENROUTER_API_KEY")
nlp-service/api/config/settings.py:36:OPENROUTER_BASE_URL: str = os.getenv(
nlp-service/api/config/settings.py:39:LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen/qwen3.5-35b-a3b")
nlp-service/api/config/settings.py:40:LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "1000"))
nlp-service/api/config/settings.py:43:NER_MODEL: str = os.getenv(
nlp-service/api/config/settings.py:46:NER_MIN_OCCURRENCES: int = int(os.getenv("NER_MIN_OCCURRENCES", "5"))
nlp-service/api/config/settings.py:49:KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
nlp-service/api/config/settings.py:52:CALLBACK_BASE_URL: str = os.getenv("CALLBACK_BASE_URL", "http://django:8000")
```

14 env-var reads total, all in `settings.py`. No env-var reads in `app.py`, `llm_engine.py`, `transformers_engine.py`, or `kafka/producer.py` (they access settings via the `settings` module).

### Env vars by category

| Category     | Variable               | Default                              | Required |
|--------------|------------------------|--------------------------------------|----------|
| App          | APP_ENV                | development                          | No       |
| CORS         | CORS_ALLOW_ORIGINS     | * (dev) / "" (prod)                  | No       |
| CORS         | CORS_ALLOW_CREDENTIALS | true                                 | No       |
| Celery       | CELERY_BROKER_URL      | redis://localhost:6379/0             | No       |
| Celery       | CELERY_RESULT_BACKEND  | same as BROKER_URL                   | No       |
| LLM          | OPENROUTER_API_KEY     | None                                 | Yes*     |
| LLM          | OPENROUTER_BASE_URL    | https://openrouter.ai/api/v1         | No       |
| LLM          | LLM_MODEL              | qwen/qwen3.5-35b-a3b                 | No       |
| LLM          | LLM_MAX_TOKENS         | 1000                                 | No       |
| NER          | NER_MODEL              | dbmdz/bert-large-cased-finetuned-... | No       |
| NER          | NER_MIN_OCCURRENCES    | 5                                    | No       |
| Kafka        | KAFKA_BOOTSTRAP_SERVERS| localhost:9092                       | No       |
| Callback     | CALLBACK_BASE_URL      | http://django:8000                   | No       |

*OPENROUTER_API_KEY is technically optional (defaults to None), but LLM features (relations) fail without it.

---

# NLP Service Audit — Task 2: Request Validation & API Behavior

## Step 1 — Payload Field Access vs. Model Definitions

### analyse.py (ChapterContentPayload)
```
line 20: payload.content        → model: content (str, max 100k)           ✓
line 22: payload.chapterId      → model: chapterId (int|str)               ✓
line 25: payload.content        → same field                               ✓
```

### ner.py (ChapterContentPayload)
```
line 20: payload.content        → model: content (str, max 100k)           ✓
line 22: payload.chapterId      → model: chapterId (int|str)               ✓
line 25: payload.content        → same field                               ✓
```

### find_pairs.py (BookFindPairsPayload)
```
line 24: payload.content        → model: content (str, max 100k)           ✓
line 26: payload.bookId         → model: bookId (int|str)                  ✓
line 29: payload.characters     → model: characters (dict[str,int])        ✓
line 32: payload.content        → same field                               ✓
```

### relations.py (BookRelationsPayload)
```
line 25: payload.bookId         → model: bookId (int|str)                  ✓
line 28: payload.pairs          → model: pairs (list[PairSentences])       ✓
line 31: pair.model_dump()      → iterates list[PairSentences]             ✓
```

**Result:** No field name mismatches. All payload fields accessed in routers map correctly to defined Pydantic models.

## Step 2 — Response Model & Status Code Declaration

| Endpoint              | File               | Line | Declaration                         |
|-----------------------|--------------------|------|-------------------------------------|
| analyse               | analyse.py         | 14   | response_model=AcceptedResponse     |
| analyse               | analyse.py         | 15   | status_code=202                     |
| analyse (error)       | analyse.py         | 21   | HTTPException status_code=422       |
| analyse (error)       | analyse.py         | 23   | HTTPException status_code=422       |
| ner                   | ner.py             | 13   | status_code=202                     |
| ner                   | ner.py             | 14   | response_model=AcceptedResponse     |
| ner (error)           | ner.py             | 21   | HTTPException status_code=422       |
| ner (error)           | ner.py             | 23   | HTTPException status_code=422       |
| find-pairs            | find_pairs.py      | 18   | response_model=AcceptedResponse     |
| find-pairs            | find_pairs.py      | 19   | status_code=202                     |
| find-pairs (error)    | find_pairs.py      | 25   | HTTPException status_code=422       |
| find-pairs (error)    | find_pairs.py      | 27   | HTTPException status_code=422       |
| relations             | relations.py       | 18   | response_model=AcceptedResponse     |
| relations             | relations.py       | 19   | status_code=202                     |
| relations (error)     | relations.py       | 26   | HTTPException status_code=422       |
| relations (error)     | relations.py       | 29   | HTTPException status_code=422       |

All four endpoints declare `response_model=AcceptedResponse` with `status_code=202`. Error paths use `HTTPException(status_code=422)`. ✓

### Concern: `analyse` endpoint blocks before responding despite 202

`analyse.py:25` uses `await asyncio.to_thread(process_analyse, ...)` before returning. This means the HTTP request blocks until `process_analyse` completes, even though the endpoint advertises status 202 (Accepted — implying processing continues asynchronously). If `process_analyse` takes significant time, the connection may time out before the response is sent. The other three endpoints correctly return 202 before the background work finishes.

### Concern: No error feedback from background execution

`find_pairs.py:31-32` uses `run_in_executor` with a `future.add_done_callback` that only logs errors — the client gets a 202 regardless of whether the executor actually succeeds. Same pattern in `relations.py:32-40` with `asyncio.create_task` + logging callback. The client has no way to know if the background work started successfully beyond the task/executor submission not raising an immediate exception.

## Step 3 — Rate Limiting Placement

```
relations.py:21:  @limiter.limit("30/minute")
ner.py:16:        @limiter.limit("30/minute")
```

Only `relations` and `ner` are rate-limited. `analyse` and `find-pairs` have no rate limits.

| Endpoint   | Rate Limited | Limit        |
|------------|:------------:|--------------|
| analyse    | No           | —            |
| ner        | Yes          | 30/minute    |
| find-pairs | No           | —            |
| relations  | Yes          | 30/minute    |

**Observation:** `analyse` is a pure-statistics synchronous function — low risk if it remains unlimited. `find-pairs` however runs an executor thread per request, which could exhaust the thread pool under load. Adding a rate limit to `find-pairs` should be considered.

## Step 4 — Edge Case Validation Gaps

### find_pairs.py — Silent acceptance of empty characters

`find_pairs.py:29`:
```python
names = list((payload.characters or {}).keys())
```

The endpoint rejects empty `content` (line 24) but silently accepts empty `characters`. When `characters` is empty (or missing, model defaults to `{}`), `names` becomes an empty list, and `process_find_pairs` is called with zero character names. This produces no useful output and wastes resources. Should either:
- Reject the request with 422 when `characters` is empty, OR
- Return 200 immediately (no work to do).

### relations.py — No per-element validation on pairs

`relations.py:27-29`:
```python
if not payload.pairs:
    raise HTTPException(status_code=422, detail="pairs list cannot be empty")
```

This validates that `pairs` is non-empty at the list level, but does not validate individual `PairSentences` elements:

| Check                          | Validated? | Issue                                            |
|--------------------------------|:----------:|--------------------------------------------------|
| `pairs` list non-empty         | Yes        | line 28                                          |
| Each `pair` has exactly 2 names| No         | `PairSentences.pair: list[Name]` — no min/max len |
| Each `pair` has non-empty `sentences` | No  | `PairSentences.sentences: list[Sentence]`         |
| Each `pair` names are valid    | No         | `Name` has max_length=100 but no other validation |
| Each sentence within max length| Via model  | `Sentence` = Annotated str with max 2000 chars    |

A pair with one element: `{"pair": ["Alice"], "sentences": ["..."]}` would pass validation and be sent to the LLM, likely producing garbage output at API cost. Similarly, empty `sentences` would waste an LLM call.

**Recommended:** Add `min_length=2, max_length=2` constraint on `PairSentences.pair` and `min_length=1` on `PairSentences.sentences` in the model, OR validate in the router before dispatching.
