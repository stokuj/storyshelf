# StoryShelf

Full-stack book tracking and literary analysis platform. Django REST API + Vue 3 SPA +
FastAPI NLP microservice, orchestrated via Docker Compose.

## Architecture

```
Browser → Vite dev proxy (5173) → Django (8000) → PostgreSQL
                                  → RabbitMQ → Celery workers → NLP service (8000)
                                  → Redis
         ↔ NLP service (8000) — character extraction, relation analysis
```

Four services in `infra/compose/docker-compose.dev.yml`: `frontend`, `django`,
`celery-worker`, `nlp-service`. Backing services: `db` (Postgres 16), `rabbitmq`,
`redis`.

`backend/` is legacy Java Spring Boot — all current work is in `backend-django/`.

## Commands

```bash
# Full dev environment
make dev-up        # docker compose -f infra/compose/docker-compose.dev.yml up -d
make dev-down
make dev-build     # rebuild images

# ── Django backend (backend-django/) ─────────────────────────────
uv run python manage.py check              # validate config
uv run python manage.py migrate            # apply migrations
uv run python manage.py runserver 0.0.0.0:8000

# Django tests — run from backend-django/ with DJANGO_ENV=dev
DJANGO_ENV=dev uv run python manage.py test                    # all tests
DJANGO_ENV=dev uv run python manage.py test books              # single app
DJANGO_ENV=dev uv run python manage.py test books.tests.test_views.BookDetailTest  # single class

# Spin up a test DB with Docker then:
DJANGO_ENV=dev DATABASE_URL=postgres://postgres:secret-key@localhost:5432/booksdb \
  uv run python manage.py test

# ── NLP service (nlp-service/) ──────────────────────────────────
uv run pytest                                  # unit tests only (default)
uv run pytest -m integration                   # integration tests
uv run pytest test/unit/test_book_service.py   # single file
uv run pytest test/unit/test_book_service.py::TestAnalyseText::test_analyse_text_counts_basic  # single test

uv run fastapi dev api/app.py                  # dev server

# ── Frontend (frontend/) ────────────────────────────────────────
npm run dev          # vite dev server (port 5173, proxies /api → localhost:8080)
npm run build        # vite build
npm run preview      # serve production build locally

# ── Production ──────────────────────────────────────────────────
make prod-up
make prod-logs
```

## Setup

```bash
cp infra/.env.example .env
# edit .env — at minimum set OPENROUTER_API_KEY for NLP features
make dev-up
```

Django uses `uv` (Python 3.13+), frontend uses `npm`. Set `DJANGO_ENV=dev` for
local development — this enables DEBUG, eager Celery (no broker), and wide CORS.

## Environment Variables

All services read from `.env` at repo root. Key vars:

| Variable | Required | Default |
|----------|----------|---------|
| `OPENROUTER_API_KEY` | for NLP | `sk-dummy-api-key` |
| `DJANGO_SECRET_KEY` | yes | `dev-secret-key` |
| `DJANGO_ENV` | yes | `dev` |
| `DATABASE_URL` | yes | `postgres://postgres:secret-key@db:5432/booksdb` |
| `CELERY_BROKER_URL` | yes | `amqp://rabbitmq:5672//` |
| `NLP_SERVICE_URL` | yes | `http://nlp-service:8000` |
| `LLM_MODEL` | no | `qwen/qwen3.5-35b-a3b` |
| `NER_MODEL` | no | `dbmdz/bert-large-cased-finetuned-conll03-english` |

Django settings: `backend-django/config/settings/__init__.py` reads `DJANGO_ENV`
and loads `dev.py` or `prod.py` on top of `base.py`.

## Conventions

### Python (Django + NLP)

- **Imports**: stdlib → third-party → local, separated by blank line
- **NLP service**: always `from __future__ import annotations`, type hints
  everywhere (`int | str`, `dict[str, Any]`), docstrings on all public functions
- **Django models**: snake_case fields, explicit string FK references for
  cross-app models (`"library.Author"`), `related_name` on every FK/M2M
- **Django serializers**: use camelCase field names when the frontend expects
  them (`mentionCount = serializers.IntegerField(source="mention_count")`)
- **Django URLs**: all paths end with trailing slash
- **Django views**: class-based (generics), custom permission classes defined
  inline in views.py, `pagination_class = None` where frontend expects flat arrays
- **Django tests**: `tests/` subdirectory per app, `__init__.py` only (no test
  content yet — tests are planned)
- **NLP tests**: `test/unit/` and `test/integration/`, mark integration tests
  with `@pytest.mark.integration`, conftest sets `OPENROUTER_API_KEY=fake-key`
- **Formatting**: no formatter configured yet. Ruff cache exists in `.ruff_cache/`
  but both `pyproject.toml` files lack `[tool.ruff]` sections. Add one when
  introducing linting.

### Frontend (Vue 3)

- Vue 3 Composition API with `<script setup>`
- Vue Router with `createWebHistory`
- API calls centralized in `src/api.js` — all functions use the shared `request()`
  helper which handles JWT tokens and silent refresh on 401
- Auth state in `src/auth.js` as a reactive singleton
- UI strings in Polish
- Tailwind CSS + daisyUI for styling
- `src/composables/useAsyncState.js` for loading/error/success state in views
- No test framework configured for frontend yet

### Git

- Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`
- Use git worktrees — never work on main directly
- PR descriptions follow Why/What/How/Testing/Rollback/Risk template

## Gotchas

- **The `Serie` model** (library/models.py) is intentionally named "Serie" (not
  "Series") because the plural "Series" clashes with Django's internal test
  discovery machinery.
- **Django settings are env-switched**: `DJANGO_ENV=dev` enables `DEBUG=True`,
  `CELERY_TASK_ALWAYS_EAGER=True` (tasks run synchronously, no broker needed),
  and `CORS_ALLOW_ALL_ORIGINS=True`. `DJANGO_ENV=prod` enables SSL redirects,
  secure cookies, HSTS.
- **NLP service module-level API key check**: `llm_service = LLMService()` at
  module level in `llm_engine.py`. Tests must set `OPENROUTER_API_KEY` before
  import (conftest.py does this).
- **Frontend proxy target**: Vite proxies `/api` to `VITE_API_PROXY_TARGET`
  (default `http://localhost:8080`). Docker Compose overrides this to
  `http://django:8000`.
- **Trailing slashes in API calls**: the frontend `api.js` appends trailing
  slashes on all paths — Django URL patterns expect them.
- **NLP integration tests** require external services (Redis, Celery) — they
  are excluded by default via `pytest` config `addopts = "-m 'not integration'"`.
- **No Kafka**: README still mentions Kafka but it was replaced with HTTP
  callbacks from NLP → Django in commit `22acdae`.
- **The `backend/` directory** is legacy Java code. All active backend work is
  in `backend-django/`.
