# StoryShelf

Full-stack book tracking and literary analysis platform. Django REST API + Vue 3 SPA,
orchestrated via Docker Compose. NER and LLM engines run inside Celery workers.

## Architecture

```
Browser → Vite dev proxy (5173) → Django (8000) → PostgreSQL
                                  → RabbitMQ → celery-ner (prefork) / celery-llm (gevent)
                                  → Redis
         ↔ Flower (5555) — Celery monitoring
```

Service containers in `infra/compose/docker-compose.dev.yml`: `frontend`,
`django`, `celery-ner`, `celery-llm`, `flower`. Backing services: `db`
(Postgres 16), `rabbitmq` (3-management-alpine), `redis`.

Architecture decisions: `ARCHITECTURE.md`. Entity models: `BookCharacter`,
`BookPlace`, `BookOrganization` (name UNIQUE, no junction tables),
`CharacterRelationship` (per book between global characters). Chapter NER
results are temporary JSON in `Chapter.ner_pending`, cleared after
`merge_book_ner` upserts into global tables.

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

# Seed test data (20 books, 17 authors, 57 tags)
uv run python ../infra/scripts/seed.py      # run from backend-django/

# Django tests — run from backend-django/ with DJANGO_ENV=dev
DJANGO_ENV=dev uv run python manage.py test                    # all tests
DJANGO_ENV=dev uv run python manage.py test books              # single app
DJANGO_ENV=dev uv run python manage.py test books.tests.test_views.BookDetailTest  # single class

# Spin up a test DB with Docker then:
DJANGO_ENV=dev DATABASE_URL=postgres://postgres:secret-key@localhost:5432/booksdb \
  uv run python manage.py test

# ── Django linting ──────────────────────────────────────────────
uv run ruff check .                                 # lint backend-django/
uv run ruff check --fix .                           # auto-fix lint issues

# ── Django celery/monitoring ────────────────────────────────────
make dev-up                                        # starts celery-ner, celery-llm, flower too
# Flower dashboard at http://localhost:5555

# ── Frontend (frontend/) ────────────────────────────────────────
npm run dev          # vite dev server (port 5173, proxies /api → localhost:8080)
npm run build        # vite build
npm run preview      # serve production build locally
npm test             # vitest (jsdom environment)
npm run test:watch   # vitest in watch mode

# Seed data in Docker
docker compose -f infra/compose/docker-compose.dev.yml exec django python ../infra/scripts/seed.py

# ── Production ──────────────────────────────────────────────────
make prod-up
make prod-logs
```

## Setup

```bash
cp .env.example .env
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
- **NLP tests**: `tests/` subdirectory per analysis app, conftest sets
  `OPENROUTER_API_KEY=fake-key`. Run with `DJANGO_ENV=dev uv run python -m pytest analysis/tests/`
- **Formatting**: Ruff configured in `backend-django/pyproject.toml` with
  `select = ["E", "F", "I", "N"]`, line-length=100, target-version=py313.
  Run `uv run ruff check .` from backend-django/.

### Frontend (Vue 3)

- Vue 3 Composition API with `<script setup>`
- Vue Router with `createWebHistory`
- API calls centralized in `src/api.js` — all functions use the shared `request()`
  helper which handles JWT tokens and silent refresh on 401
- Auth state in `src/auth.js` as a reactive singleton
- UI strings in Polish
- Tailwind CSS + daisyUI (themes: `light`, `dark`)
- `src/composables/useAsyncState.js` for loading/error/success state in views
- Shared components: `AlertMessage.vue`, `LoadingSpinner.vue`, `BookCard.vue` in `src/components/`
- Tests: Vitest + jsdom (`npm test`), test files in `__tests__/` subdirectories
- **Router handles auth initialization**: `router.beforeEach` calls `refreshAuth()`
  on first navigation if `authState.initialized` is false. App.vue does NOT need
  `onMounted` for this — the router guard handles it before any route renders.

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
- **Frontend proxy target**: Vite proxies `/api`, `/admin`, and `/static` to
  `VITE_API_PROXY_TARGET` (default `http://django:8000`). Docker Compose
  overrides this to `http://django:8000`.
- **Trailing slashes in API calls**: the frontend `api.js` appends trailing
  slashes on all paths — Django URL patterns expect them.
- **No Kafka**: README still mentions Kafka but it was replaced with HTTP
  callbacks from NLP → Django in commit `22acdae`.
- **The `backend/` directory** is legacy Java code. All active backend work is
  in `backend-django/`.
- **DRF pagination**: Frontend expects flat arrays, NOT `{count, results}`.
  Always set `pagination_class = None` on list endpoints consumed by the
  frontend (books, shelf, reviews, characters, relations, followers, following).
- **DRF field naming**: Frontend expects `camelCase`. Always map snake_case
  fields via `serializers.IntegerField(source="snake_name")` or similar.
- **Docker volume mounts**: Never bind-mount a host directory that contains
  a `.venv/` (the host Python version may differ). Always add `.venv/` to
  `.dockerignore`. Use the built image directly in dev compose.
- **Alpine healthcheck**: Alpine `wget` resolves `localhost` to `::1` (IPv6)
  but Vite listens on IPv4 only. Use `127.0.0.1` explicitly in healthcheck.
- **RabbitMQ version**: Pin to `rabbitmq:3-management-alpine`. Version 4
  deprecates `transient_nonexcl_queues`, breaking Celery 5.6.
- **NLP Kafka removed**: Kafka consumer/producer replaced with HTTP callbacks
  to Django (`/api/internal/*`). `confluent-kafka` removed from dependencies.
- **Seed data**: Use `infra/scripts/seed.py` (idempotent, `get_or_create`).
  Creates 20 books + 17 authors + 57 tags.
- **Frontend Docker rebuild**: The frontend Dockerfile copies files at build time
  (`COPY . .`) — no volume mount. Host changes require `make dev-build` +
  `make dev-up` to take effect in the running container. For quick local
  verification without Docker, use `cd frontend && npm run build`.
- **Testing from a worktree**: Docker compose builds frontend from the main
  worktree context. To test changes from a secondary worktree, rebuild manually:
  ```bash
  docker build -t storyshelf-frontend:local /path/to/worktree/frontend/
  docker compose -f infra/compose/docker-compose.dev.yml up -d frontend
  ```
- **Nginx location priority**: When combining prefix proxy locations (`/api/`)
  with regex asset locations (`~*`), use `location ^~ /api/` to give the prefix
  higher priority than the regex pattern. Without `^~`, an asset request to
  `/api/something.js` would match the regex cache location instead of the proxy.
- **Frontend auth init**: The `beforeEach` guard calls `await refreshAuth()` if
  `authState.initialized` is false. This ensures `authenticated` is checked
  before `requiresAuth` routes reject the user on F5.
- **Celery worker pools**: `celery-ner` uses `--pool prefork` (CPU-bound BERT),
  `celery-llm` uses `--pool gevent` (I/O-bound OpenRouter). Tasks are routed via
  `CELERY_TASK_ROUTES`: analysis/stats/ner/merge → `ner` queue,
  `relations_for_book` → `llm` queue.
- **Flower**: Monitoring dashboard at `http://localhost:5555`, shows both worker
  pools. Started automatically with `make dev-up`.
- **RabbitMQ DLX**: Dead letter exchange defined in `infra/rabbitmq/definitions.json`.
  Failed tasks (after max retries) land in `dead_letter` queue. Inspect via
  RabbitMQ management UI (`http://localhost:15672`).
- **Entity models**: `BookCharacter`, `BookPlace`, `BookOrganization` have
  `name UNIQUE` — no junction tables. Characters per book queried from global
  pool. `CharacterRelationship` has `book` FK for per-book scoping.
- **Chapter ner_pending**: Temporary JSON field cleared after `merge_book_ner`
  upserts into global entity tables and clears `chapter.text`.
- **NER_MIN_OCCURRENCES**: Env var (default 5) filters low-frequency entities.
  When testing `extract_entities`, mock or set to 1 to test with small inputs.
- **Genre model**: `Genre` lives in `library/models.py`, `BookGenre` through table
  in `books/models.py`. Frontend expects `genres` as array of strings from
  API — serializers use `SerializerMethodField` for this.
- **CI/CD**: Pipeline in `.github/workflows/ci.yml` (ruff lint, Django tests,
  Docker build, push to GHCR). Deploy step is commented out — ready to enable.
- **Caddy HTTPS**: Prod Caddyfile uses `tls internal` (self-signed). For
  production with real certs, replace with Let's Encrypt configuration.
- **Root `.dockerignore`** now exists — docker builds from subdirectories
  (frontend/, backend-django/) also have their own `.dockerignore`.
- **`infra/.env.example` removed** — use only root `.env.example`.
