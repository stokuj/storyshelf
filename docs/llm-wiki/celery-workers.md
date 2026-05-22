---
title: Celery Workers
last_updated: 2026-05-22
last_verified_commit: 86ea9b0
owns:
  - backend-django/config/celery.py
  - infra/compose/docker-compose.dev.yml
  - infra/compose/docker-compose.prod.yml
  - infra/rabbitmq/definitions.json
depends_on:
  - RabbitMQ 3.x (message broker)
  - Redis (result backend)
  - Flower (monitoring)
related_pages: [nlp-pipeline, dev-setup]
status: stable
---

## Co to jest

Dwa osobne workery Celery obsługujące pipeline NLP: `celery-ner` (CPU-bound, spaCy) i
`celery-llm` (I/O-bound, OpenRouter). Każdy ma własną kolejkę RabbitMQ, własny typ pool,
własny kontener Docker.

## Jak działa

```
Django (analyse_book.delay) → RabbitMQ
    │
    ├── exchange: default (direct)
    │
    ├── queue: ner   → celery-ner (--pool prefork --concurrency 1)
    │                    └── analyse_book, statystyki tekstu
    │
    ├── queue: llm   → celery-llm (--pool gevent --concurrency 10)
    │                    └── relations_for_book
    │
    └── dead letter exchange: dlx → queue: dead_letter
            └── failed tasks (po max_retries) — inspekcja przez RabbitMQ management UI

Result backend: Redis (TTL ~24h)
Monitoring: Flower :5555 — pokazuje oba workery
```

Routing przez `CELERY_TASK_ROUTES` w `backend-django/config/celery.py`:
```python
task_routes = {
    "analysis.tasks.analyse_book": {"queue": "ner"},
    "analysis.tasks.stats_*": {"queue": "ner"},
    "analysis.tasks.relations_for_book": {"queue": "llm"},
}
```

W dev (`DJANGO_ENV=dev`): `CELERY_TASK_ALWAYS_EAGER=True` — taski wykonują się synchronicznie
w procesie Django bez brokera. RabbitMQ + workery niepotrzebne dla testów.

## Decyzje

- Dwa pools, dwa workery: patrz [ADR-002](../decisions/ADR-002-dwa-workery-celery.md)
- DLX zamiast nieskończonych retry: zadania, które padają max_retries razy, idą do
  dead_letter zamiast spamować logi i blokować pool
- gevent dla LLM: ~10 równoległych zapytań HTTP do OpenRouter wystarcza dla typowej książki
  (~50-200 par postaci), bez konieczności asyncio rewrite

## Typowe operacje

**Uruchomienie workerów lokalnie (poza Docker):**
```bash
# Terminal 1 — celery-ner
cd backend-django
DJANGO_ENV=dev uv run celery -A config worker --queues ner --pool prefork --concurrency 1

# Terminal 2 — celery-llm
DJANGO_ENV=dev uv run celery -A config worker --queues llm --pool gevent --concurrency 10

# Terminal 3 — Flower
DJANGO_ENV=dev uv run celery -A config flower --port 5555
```

**Sprawdzenie kolejek w RabbitMQ:**
- Management UI: `http://localhost:15672` (guest/guest w dev)
- Sprawdź queues `ner`, `llm`, `dead_letter` — message count, consumers

**Monitoring w Flower:**
- `http://localhost:5555` — workers, tasks, broker status
- Pokazuje oba workery: `celery@<hostname>-ner` i `celery@<hostname>-llm`

**Inspekcja DLQ:**
```bash
# Z kontenera RabbitMQ
docker compose -f infra/compose/docker-compose.dev.yml exec rabbitmq \
  rabbitmqctl list_queues name messages | grep dead_letter
```

**Restart pojedynczego workera:**
```bash
docker compose -f infra/compose/docker-compose.dev.yml restart celery-ner
```

## Pułapki

- **RabbitMQ pin do `3-management-alpine`** — wersja 4 deprecates `transient_nonexcl_queues`,
  łamie Celery 5.6. Nie aktualizuj bez testów.
- **`definitions.json` musi mieć vhosts pierwsze** — bez deklaracji `"vhosts": [{"name": "/"}]`
  przed exchanges/queues RabbitMQ 3.x crashuje przy starcie z błędem "Please create virtual
  host '/' prior to importing definitions."
- **`CELERY_TASK_ALWAYS_EAGER=True` w dev** — taski są synchroniczne, błędy lecą inline.
  W prod (`DJANGO_ENV=prod`) eager off, taski idą przez broker.
- **gevent monkey-patch**: import order matters. `celery-llm` worker musi wywołać
  `gevent.monkey.patch_all()` **przed** importem requests/openrouter SDK.
- **Pool prefork dla NER**: nie używaj gevent — spaCy/torch C-extensions nie współpracują
  z monkey-patched threading.
- **`--concurrency 1` dla celery-ner**: model spaCy ładuje się raz przy starcie workera
  (~kilkaset MB), więcej procesów = wielokrotne ładowanie modelu = OOM na VPS.
- **Flower auth w prod**: domyślnie brak auth. W prod skonfiguruj basic auth przez
  `--basic_auth=user:pass`.
- **Result expiry**: Redis czyści wyniki po 24h (`CELERY_RESULT_EXPIRES = 86400`).
  Dla długich audytów ustaw wyżej lub zapisuj wyniki w PG zamiast w Redis.

## Pytania, na które ta strona odpowiada

- Jak uruchomić workery lokalnie bez Dockera?
- Czemu są 2 osobne workery zamiast jednego?
- Gdzie są tracene failed tasks?
- Jak sprawdzić, czy NER task się wykonał?
- Czemu mój LLM task nie używa parallelism mimo `--concurrency 10`?
- Co robi `CELERY_TASK_ALWAYS_EAGER`?
- Jak skalować Celery na VPS?
- Czemu RabbitMQ pinned na 3.x a nie 4.x?
- Jak Django woła zadanie Celery? (patrz [[nlp-pipeline]])
