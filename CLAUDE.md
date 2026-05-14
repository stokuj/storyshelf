# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Full conventions, gotchas, and detailed architecture are in **AGENTS.md**. Read it before working on any non-trivial task.

## What This Project Is

StoryShelf — book-tracking + literary analysis platform.
Django 6 REST API + Vue 3 SPA, orchestrated via Docker Compose.
NER (spaCy en_core_web_trf, CPU-only) and LLM (OpenRouter) run inside Celery workers.

All backend work is in `backend-django/`. There is no `backend/` directory anymore.

## Key Commands

### Backend (run from `backend-django/` using `uv`)

```bash
# Run / check
uv run python manage.py runserver 0.0.0.0:8000
uv run python manage.py check
uv run python manage.py migrate

# Tests — DJANGO_ENV=dev is required
DJANGO_ENV=dev uv run python manage.py test                                          # all tests
DJANGO_ENV=dev uv run python manage.py test books                                    # single app
DJANGO_ENV=dev uv run python manage.py test books.tests.test_views.BookDetailTest    # single class

# NLP tests use pytest
DJANGO_ENV=dev uv run python -m pytest analysis/tests/

# Lint
uv run ruff check .          # check
uv run ruff check --fix .    # auto-fix
```

### Frontend (run from `frontend/`)

```bash
npm run dev      # Vite dev server on port 5173
npm test         # Vitest (jsdom) — run all tests
npm run test -- src/views/__tests__/BookDetailView.test.js   # single test file
npm run build    # production build (no sourcemaps)
```

### Docker dev stack

```bash
make dev-up     # all services (db, redis, rabbitmq, django, celery-ner, celery-llm, flower, frontend)
make dev-down
make dev-build  # rebuild images
make dev-superuser  # create Django superuser in container
make verify     # lint + tests (CI equivalent)
```

Seed test data (20 books, idempotent):
```bash
uv run python ../infra/scripts/seed.py   # from backend-django/
```

## Django App Layout

```
backend-django/
  books/        — Book (+ Book.text for NLP upload), BookAuthor, BookGenre; list/detail/search
  library/      — Author, Genre, Serie, Tag models
  users/        — auth (JWT), user profile, follow system
  shelf/        — ShelfEntry (want_to_read / reading / read per user per book)
  reviews/      — Review (1 per user per book, rating 1–5); signals update Book.avg_rating
  analysis/     — NER + LLM Celery tasks, BookCharacter/Place/Organization/CharacterRelationship
  config/       — settings (base/dev/prod), urls.py, celery.py
```

API root: `http://localhost:8000/api/`
Swagger docs: `http://localhost:8000/api/docs/`

## Frontend Layout

```
frontend/src/
  api.js              — all HTTP calls, JWT attach + silent 401 refresh
  auth.js             — reactive authState singleton, refreshAuth(), signOut()
  router.js           — Vue Router, auth guard on requiresAuth routes
  composables/
    useAsyncState.js  — loading/error/message state; execute(fn, {timeout, fallback})
  views/              — 7 page-level components
  components/         — AlertMessage, BookCard, LoadingSpinner, NotFoundState
```

Tests: Vitest + @vue/test-utils + jsdom. Files in `__tests__/` subdirectories.

## NLP Pipeline

```
Admin uploads text → Book.text
Admin triggers → analyse_book.delay(book_id)   [queue: ner, CPU-bound]
    - spaCy en_core_web_trf on fixed-size chunks (400 words, overlap 50)
    - saves BookCharacter/Place/Organization per book (book FK)
    - find_pairs() synchronously → relations_for_book.delay()
    - clears Book.text after analysis

relations_for_book(book_id, pairs_data)         [queue: llm, I/O-bound]
    - LLM (OpenRouter) per character pair → CharacterRelationship
    - errors per pair: log + skip, no retry
```

NER engine: `analysis/ner_engine.py` — `chunk_text()` + `extract_entities_from_chunks()`
Entities are **per-book** (`unique_together("name", "book")`), not global.

## Settings

`config/settings/__init__.py` reads `DJANGO_ENV` and loads `dev.py` or `prod.py` on top of `base.py`.

`DJANGO_ENV=dev` enables: `DEBUG=True`, `CELERY_TASK_ALWAYS_EAGER=True` (no broker needed), `CORS_ALLOW_ALL_ORIGINS=True`, `CSRF_TRUSTED_ORIGINS=["http://localhost:5173"]`.

## Critical Gotchas

- **`DJANGO_ENV=dev` required for tests** — without it, settings won't load correctly.
- **Pagination**: Frontend expects flat arrays. Always `pagination_class = None` on list endpoints.
- **Field naming**: Frontend expects camelCase — map via `serializers.IntegerField(source="snake_name")`.
- **`avg_rating` not `rating`**: `BookSerializer` exposes `avg_rating` and `ratingsCount`. Frontend must use `book.avg_rating` — `book.rating` is undefined.
- **`relation_type` not `relation`**: `CharacterRelationSerializer` exposes `relation_type`. No `evidence` field exists.
- **`Serie` model** is intentionally singular (not `Series`) — "Series" clashes with Django test discovery.
- **RabbitMQ**: Pin to `rabbitmq:3-management-alpine` (v4 breaks Celery 5.6). `definitions.json` must declare `"vhosts": [{"name": "/"}]` first.
- **Trailing slashes**: All Django URL patterns and all `api.js` frontend calls use trailing slashes.
- **LLM module-level init**: `LLMService()` instantiates at import time — `analysis/tasks.py` wraps the import in `try/except` so tests don't fail when `OPENROUTER_API_KEY` is missing.
- **`NER_MIN_OCCURRENCES`** defaults to 5 — set to 1 when testing NER with small inputs.
- **spaCy Python version**: `pyproject.toml` pins `requires-python = ">=3.13,<3.14"` because `en_core_web_trf` has no cp314 wheel yet. Production runs 3.13.
- **No Chapter model** — removed. Book text lives in `Book.text`, cleared after NLP analysis.
- **BookDetail response**: `{book, shelfEntry, characters, relations}` — no `chapters` key.
- **`analyse_book` is not idempotent on re-run** — re-uploading text and re-running accumulates entities. Delete `BookCharacter/Place/Organization` manually for a clean re-analysis.
- **JWT in localStorage** — XSS-vulnerable. HttpOnly cookie migration is pending. Do not add new localStorage token reads outside `src/api.js`.
- **`useAsyncState` timeout** — `execute(fn, { timeout: ms })` default 15 000 ms. On timeout shows Polish error `'Przekroczono czas oczekiwania.'`.

## Conventions

- Class-based DRF views (generics), custom permissions defined inline in `views.py`.
- Explicit string FK references for cross-app models: `"library.Author"`.
- `related_name` on every FK/M2M.
- Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`.
- Reset DB instead of writing manual migrations during development: `manage.py flush --no-input && manage.py migrate`.
