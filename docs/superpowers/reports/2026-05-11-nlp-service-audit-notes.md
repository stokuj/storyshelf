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

### nlp-service/api/routers/analyse.py (ChapterContentPayload)
```
line 20: payload.content        → model: content (str, max 100k)           ✓
line 22: payload.chapterId      → model: chapterId (int|str)               ✓
line 25: payload.content        → same field                               ✓
```

### nlp-service/api/routers/ner.py (ChapterContentPayload)
```
line 20: payload.content        → model: content (str, max 100k)           ✓
line 22: payload.chapterId      → model: chapterId (int|str)               ✓
line 25: payload.content        → same field                               ✓
```

### nlp-service/api/routers/find_pairs.py (BookFindPairsPayload)
```
line 24: payload.content        → model: content (str, max 100k)           ✓
line 26: payload.bookId         → model: bookId (int|str)                  ✓
line 29: payload.characters     → model: characters (dict[str,int])        ✓
line 32: payload.content        → same field                               ✓
```

### nlp-service/api/routers/relations.py (BookRelationsPayload)
```
line 25: payload.bookId         → model: bookId (int|str)                  ✓
line 28: payload.pairs          → model: pairs (list[PairSentences])       ✓
line 31: pair.model_dump()      → iterates list[PairSentences]             ✓
```

**Result:** No field name mismatches. All payload fields accessed in routers map correctly to defined Pydantic models.

## Step 2 — Response Model & Status Code Declaration

| Endpoint              | File               | Line | Declaration                         |
|-----------------------|--------------------|------|-------------------------------------|
| analyse               | nlp-service/api/routers/analyse.py         | 14   | response_model=AcceptedResponse     |
| analyse               | nlp-service/api/routers/analyse.py         | 15   | status_code=202                     |
| analyse (error)       | nlp-service/api/routers/analyse.py         | 21   | HTTPException status_code=422       |
| analyse (error)       | nlp-service/api/routers/analyse.py         | 23   | HTTPException status_code=422       |
| ner                   | nlp-service/api/routers/ner.py             | 13   | status_code=202                     |
| ner                   | nlp-service/api/routers/ner.py             | 14   | response_model=AcceptedResponse     |
| ner (error)           | nlp-service/api/routers/ner.py             | 21   | HTTPException status_code=422       |
| ner (error)           | nlp-service/api/routers/ner.py             | 23   | HTTPException status_code=422       |
| find-pairs            | nlp-service/api/routers/find_pairs.py      | 18   | response_model=AcceptedResponse     |
| find-pairs            | nlp-service/api/routers/find_pairs.py      | 19   | status_code=202                     |
| find-pairs (error)    | nlp-service/api/routers/find_pairs.py      | 25   | HTTPException status_code=422       |
| find-pairs (error)    | nlp-service/api/routers/find_pairs.py      | 27   | HTTPException status_code=422       |
| relations             | nlp-service/api/routers/relations.py       | 18   | response_model=AcceptedResponse     |
| relations             | nlp-service/api/routers/relations.py       | 19   | status_code=202                     |
| relations (error)     | nlp-service/api/routers/relations.py       | 26   | HTTPException status_code=422       |
| relations (error)     | nlp-service/api/routers/relations.py       | 29   | HTTPException status_code=422       |

All four endpoints declare `response_model=AcceptedResponse` with `status_code=202`. Error paths use `HTTPException(status_code=422)`. ✓

### Concern: `analyse` endpoint blocks before responding despite 202 — **Severity: MEDIUM**

`nlp-service/api/routers/analyse.py:25` uses `await asyncio.to_thread(process_analyse, ...)` before returning. This means the HTTP request blocks until `process_analyse` completes, even though the endpoint advertises status 202 (Accepted — implying processing continues asynchronously). If `process_analyse` takes significant time, the connection may time out before the response is sent. The other three endpoints correctly return 202 before the background work finishes.

### Concern: No error feedback from background execution — **Severity: HIGH**

`nlp-service/api/routers/find_pairs.py:31-32` uses `run_in_executor` with a `future.add_done_callback` that only logs errors — the client gets a 202 regardless of whether the executor actually succeeds. Same pattern in `nlp-service/api/routers/relations.py:32-40` with `asyncio.create_task` + logging callback. The client has no way to know if the background work started successfully beyond the task/executor submission not raising an immediate exception.

**Recommendation:** Return a job ID in the 202 response and add a `GET /jobs/{jobId}/status` endpoint for clients to poll completion status. Alternatively, accept an optional webhook URL in the request body and POST status updates (success/failure/result) back to the caller. The job-status approach is simpler and aligns with standard async API patterns.

## Step 3 — Rate Limiting Placement

```
nlp-service/api/routers/relations.py:21:  @limiter.limit("30/minute")
nlp-service/api/routers/ner.py:16:        @limiter.limit("30/minute")
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

### find_pairs.py — Silent acceptance of empty characters — **Severity: LOW**

`nlp-service/api/routers/find_pairs.py:29`:
```python
names = list((payload.characters or {}).keys())
```

The endpoint rejects empty `content` (line 24) but silently accepts empty `characters`. When `characters` is empty (or missing, model defaults to `{}`), `names` becomes an empty list, and `process_find_pairs` is called with zero character names. This produces no useful output and wastes resources. Should either:
- Reject the request with 422 when `characters` is empty, OR
- Return 200 immediately (no work to do).

### relations.py — No per-element validation on pairs — **Severity: MEDIUM**

`nlp-service/api/routers/relations.py:27-29`:
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

---

## Task 2 — Severity Summary

| Severity | Finding                                                                 | File(s)                                      |
|----------|-------------------------------------------------------------------------|----------------------------------------------|
| HIGH     | No error feedback from background execution                             | `find_pairs.py`, `relations.py`             |
| MEDIUM   | `analyse` blocks before responding despite 202                          | `analyse.py`                                 |
| MEDIUM   | No per-element validation on `pairs`                                    | `relations.py`                               |
| LOW      | Silent acceptance of empty characters                                   | `find_pairs.py`                              |

---

# NLP Service Audit — Task 3: Core NLP Workflows & Helper Code Audit

## Step 1 — Workflow Signature Trace

```
process_analyse({"content": "str", "chapter_id": "int | str | None"}) -> <class 'dict'>
  docstring: Analyse text and optionally send the result back to Spring.

process_ner({"content": "str", "chapter_id": "int | str | None"}) -> <class 'dict'>
  docstring: Run NER on *content* and optionally send the result back to Spring.

process_find_pairs({"content": "str", "names": "list[str]", "chapter_id": "int | str | None", "book_id": "int | str | None"}) -> <class 'list'>
  docstring: Find sentence pairs and optionally send the result back to Spring.

process_chapter_relations({"content": "str", "chapter_id": "int | str", "characters": "list[str] | None"}) -> <class 'dict'>
  docstring: Extract character relations for a whole chapter.

process_book_relations_async({"pairs": "list[dict]", "book_id": "int | str"}) -> <class 'dict'>
  docstring: (none)
```

### Return value analysis

| Function                       | Sync/Async | Return type | Callee          | Callback topic             | Fire-and-forget? |
|--------------------------------|:----------:|:-----------:|:---------------:|----------------------------|:----------------:|
| `process_analyse`              | Sync       | `dict`      | —               | `chapter.analyse.results`  | No               |
| `process_ner`                  | Sync       | `dict`      | —               | `chapter.ner.results`      | No               |
| `process_find_pairs`           | Sync       | `list[dict]`| —               | `book.find-pairs.results`  | No               |
| `process_chapter_relations`    | Sync       | `dict`      | `llm_service`   | —                          | —                |
| `process_book_relations_async` | Async      | `dict`      | `llm_service`   | `book.relations.results`   | Yes              |

**Key observations:**

1. All five workflow functions return a value *regardless* of callback success. The callbacks are side effects only — if `send_json` fails (retries exhausted), the caller still gets a valid result. **Severity: MEDIUM** — the caller (HTTP router or Celery task) may assume callback succeeded when it actually failed.

2. `process_chapter_relations` is the only workflow that does NOT send a callback. It returns the result synchronously to the caller (currently unused in any HTTP endpoint — only exists as reusable orchestration logic).

3. `process_book_relations_async` is a true fire-and-forget — the caller `asyncio.create_task`-s it and the result goes only to the callback, not to any HTTP response.

## Step 2 — LLM Error Fallback and Callback Resilience

### LLM Error Fallback — **Severity: HIGH**

`nlp-service/api/services/core/llm_engine.py:139-146` (async) and `:173-180` (sync):

```python
except (
    openai.RateLimitError,
    openai.APITimeoutError,
    openai.APIConnectionError,
    openai.APIError,
) as e:
    logger.error("API error for pair %s: %s", pair, e, exc_info=True)
    return '{"relations": []}'
```

Five OpenAI exception types are caught and **silently converted to an empty relations array**. The caller (`process_chapter_relations` or `process_book_relations_async`) parses this JSON and proceeds as if extraction succeeded with no relations found. This means:

- **Rate limit errors** (429) → logged, returned as empty relations — caller assumes no relationship exists between the character pair rather than understanding the API was throttled.
- **Timeout errors** → same treatment — pair is counted as "processed with no relations."
- **Connection errors** → same treatment — no retry at the LLM layer, no back-off.
- **General API errors** → same treatment.

The caller has **no way to distinguish** "LLM found no relations" from "the LLM API call failed entirely." This is data loss — relationships that exist in the text are silently dropped.

**Recommendation:** Return a distinguishable value (e.g., `'{"error": "rate_limit"}'`) and propagate the error to the callback topic so Django can record the failure per-pair. Alternatively, retry with exponential backoff at the LLM service layer before giving up.

### Callback Resilience — **Severity: MEDIUM**

`nlp-service/api/kafka/producer.py:24-34` (`_post_callback`): retries 3 times with exponential backoff (1s, 2s, 4s) then raises.

`nlp-service/api/kafka/producer.py:37-43` (`send_json`): catches the re-raised exception from `_post_callback`, logs it, and silently returns.

```python
def send_json(topic: str, key: str, payload: dict) -> None:
    ...
    try:
        _post_callback(url, payload)
    except Exception:
        logger.exception("Callback to %s failed after retries", url)
```

The return type is `None` — the callback is purely a side effect. Every workflow function that calls `send_json`:
- `process_analyse` (`analyse_workflow.py:22`) — returns result regardless
- `process_ner` (`ner_workflow.py:23`) — returns result regardless
- `process_find_pairs` (`find_pairs_workflow.py:29`) — returns result regardless
- `process_book_relations_async` (`relations_workflow.py:114`) — returns result regardless

No caller checks whether `send_json` succeeded. If the Django backend is down or unreachable for more than 12 seconds (3 retries * ~30s timeout), the NLP result is computed at computational cost but **never delivered to the database**. The HTTP client received a 202 — so it believes the job was accepted successfully.

**Recommendation:** At minimum, write failed callbacks to a dead-letter log or local file for later replay. Better: use Celery tasks for all callbacks so they get persistent retry with exponential backoff via the broker.

## Step 3 — Model Loading and Tokenizer Fallbacks

### NER Model Loading — **Severity: MEDIUM**

`nlp-service/api/services/core/transformers_engine.py:20-41`:

```python
_NER_PIPELINES: dict[str, Any] = {}

def load_ner_model(model: str) -> bool:
    if model in _NER_PIPELINES:
        return True
    try:
        _NER_PIPELINES[model] = pipeline(...)
        return True
    except (OSError, EnvironmentError) as e:
        logger.warning("Transformers model '%s' is not available. Skipping.", model)
        return False
```

The model pipeline is cached in a module-level `_NER_PIPELINES` dict. If the model file is unavailable (e.g., not downloaded, disk error), `load_ner_model` returns `False`. The caller `extract_entities` (`:49-50`) checks this and returns an **empty dict `{}`** — no error is raised upstream. The HTTP router in `ner.py` returns a 202 with `{"status": "Accepted"}` regardless. The callback posts an empty NER result to Django.

**Implications:**
- If the NER model was never downloaded, every NER request silently returns empty results with HTTP 202.
- The Celery worker process `worker_process_init` handler calls `load_ner_model` at startup — if it fails, the worker starts but all subsequent NER tasks return `{}`.
- No health check validates that the NER model loaded successfully.

### Tokenizer Fallback — **Severity: LOW**

`nlp-service/api/services/core/text_stats.py:16-34`:

```python
try:
    import tiktoken
except ImportError:
    tiktoken = None

def _get_tokenizer():
    global _TOKENIZER
    if _TOKENIZER is None and tiktoken is not None:
        _TOKENIZER = tiktoken.get_encoding(TOKENIZER_NAME)
    return _TOKENIZER

# In analyse_text:
if tokenizer is None:
    token_count = len(text) // 4
```

When `tiktoken` is not installed (optional dependency), the token count falls back to `len(text) // 4`. This heuristic assumes English text at ~4 characters per token. It is inaccurate for:
- Non-English text (e.g., Polish uses more tokens per word due to inflection)
- Code blocks or markup mixed with prose
- Very short or very long texts

The inaccurate token count propagates to the `analyse` result sent to Django via callback. Since this is a statistical endpoint (not critical to core features), the impact is limited.

**Recommendation:** Add a `tokenizer_available` boolean to the response or log a warning when the fallback is used, so consumers of the API can distinguish accurate counts from heuristics.

## Step 4 — LLM Prompt Injection and Correctness

### Sanitization — **Severity: MEDIUM**

`nlp-service/api/services/core/llm_engine.py:51-58`:

```python
@staticmethod
def _sanitize(text: str) -> str:
    for marker in ("```", "---", "###", "SYSTEM:", "ASSISTANT:", "USER:"):
        text = text.replace(marker, "")
    return "".join(ch for ch in text if ch == "\n" or ch >= " ")
```

The sanitization strips common prompt injection delimiters and ASCII control characters. Gaps:

1. **Unicode homoglyphs not stripped**: Fullwidth variants like `ＳＹＳＴＥＭ` (U+FF33 etc.) or zero-width joiners pass through unmodified. An attacker could inject instructions using these characters.
2. **No normalization**: The markers are only matched as literal ASCII strings. Case variations or padding with non-printable characters could bypass the check.
3. **Order sensitive**: `SYSTEM:` is removed, but `SYS` + `TEM:` (split across two parts that get reassembled by the model) would still pass.
4. **Missing markers**: No handling of `IMPORTANT`, `IGNORE PREVIOUS`, or other common injection phrases. The `###` marker removal is specifically for Markdown headers — a single `#` or `##` is not stripped.

**Recommendation:** Use a dedicated prompt-injection detection library or encode user input as a clearly delimited block (e.g., XML tags) that the model is explicitly instructed not to interpret as instructions.

### Prompt Contract and JSON Parsing — **Severity: HIGH**

`nlp-service/api/services/core/llm_engine.py:60-103` (`_get_prompt`):

The prompt instructs the model to "RETURN ONLY JSON, no text before or after." The callers parse the response with `json.loads`:

- `relations_workflow.py:81`: If `json.loads` raises `JSONDecodeError`, the result is wrapped as `{"raw": raw_string}` — no structured relations extracted.
- `relations_workflow.py:107` (async variant): Same fallback.

Problems:

1. **No output validation beyond JSON parse**: If the model returns valid JSON but with non-existent relation types, malformed evidence, or relations involving characters outside the requested pair, the data flows through unchecked.
2. **Evidence not validated against input**: The prompt requires "evidence must be a direct quote from the text" (line 90), but no post-processing verifies that the evidence string actually appears in the input sentences. The model can hallucinate plausible-sounding quotes.
3. **JSON extraction fallback is fragile**: If the model wraps JSON in markdown code fences despite the prompt (a common LLM behavior), the resulting string starts with `` ```json ``. `json.loads` fails, and the caller stores the raw markdown-wrapped string. Django receives `{"raw": "```json\n{...}\n```"}` — which it may not handle.
4. **No JSON repair**: A trailing comma in the model output (e.g., `"evidence": "quote",]}`) would cause `json.loads` to fail. Libraries like `json-repair` exist but are not used.

**Recommendation:**
1. Extract JSON from the response using regex (e.g., `re.search(r'\{.*\}', content, re.DOTALL)`) before parsing.
2. Validate that `evidence` strings are substrings of the input sentences.
3. Validate that `relation` values are in the allowed set from `RELATION_SCHEMA`.
4. Add a `json_parse_error` or `invalid_schema` flag to results so Django can distinguish real data from fallback.

## Task 3 — Severity Summary

| Severity | Finding                                                                 | File(s)                                      |
|----------|-------------------------------------------------------------------------|----------------------------------------------|
| HIGH     | LLM exceptions silently return empty relations — indistinguishable from "no relationship found" | `llm_engine.py:139-146,173-180` |
| HIGH     | No validation of LLM JSON output — evidence may be hallucinated, relation types unchecked | `llm_engine.py:60-103`, `relations_workflow.py:81-83` |
| MEDIUM   | Callback failure is silent — NLP result computed but never delivered to DB | `kafka/producer.py:37-43`, all 4 workflows |
| MEDIUM   | NER model load failure returns `{}` — no error surfaced to client or health check | `transformers_engine.py:20-41,49-50` |
| MEDIUM   | Prompt sanitization incomplete — Unicode homoglyphs and bypass techniques not covered | `llm_engine.py:51-58` |
| LOW      | Tokenizer heuristic `len(text)//4` inaccurate for non-English text | `text_stats.py:31-34` |

