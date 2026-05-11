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
