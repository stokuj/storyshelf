# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Full conventions, gotchas, and detailed architecture are in **AGENTS.md**. Read it before working on any non-trivial task.

## What This Project Is

StoryShelf — book-tracking + literary analysis platform.
Django 6 REST API + Vue 3 SPA, orchestrated via Docker Compose.
NER (BERT) and LLM (OpenRouter) run inside Celery workers.

All backend work is in `backend-django/`. There is no `backend/` directory anymore.

## Key Commands

All Django commands run from `backend-django/` using `uv`:

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

Full Docker dev stack:
```bash
make dev-up     # all services (db, redis, rabbitmq, django, celery-ner, celery-llm, flower, frontend)
make dev-down
make dev-build  # rebuild images
```

Seed test data (20 books, 17 authors, 57 tags — idempotent):
```bash
uv run python ../infra/scripts/seed.py   # from backend-django/
```

## Django App Layout

```
backend-django/
  books/        — Book, BookAuthor, BookGenre models; list/detail/search endpoints
  library/      — Author, Genre, Serie, Tag models
  users/        — auth (JWT), user profile, follow system
  shelf/        — ShelfEntry (want_to_read / reading / read per user per book)
  reviews/      — Review (1 per user per book, rating 1–5); signals update Book.avg_rating
  analysis/     — NER + LLM Celery tasks, NERResult, BookSummary, CharacterRelationship
  config/       — settings (base/dev/prod), urls.py, celery.py
```

API root: `http://localhost:8000/api/`  
Swagger docs: `http://localhost:8000/api/docs/`

## Settings

`config/settings/__init__.py` reads `DJANGO_ENV` and loads `dev.py` or `prod.py` on top of `base.py`.

`DJANGO_ENV=dev` enables: `DEBUG=True`, `CELERY_TASK_ALWAYS_EAGER=True` (no broker needed), `CORS_ALLOW_ALL_ORIGINS=True`.

## Critical Gotchas

- **`DJANGO_ENV=dev` required for tests** — without it, settings won't load correctly.
- **Pagination**: Frontend expects flat arrays. Always `pagination_class = None` on list endpoints.
- **Field naming**: Frontend expects camelCase — map via `serializers.IntegerField(source="snake_name")`.
- **`Serie` model** is intentionally singular (not `Series`) — "Series" clashes with Django test discovery.
- **RabbitMQ**: Pin to `rabbitmq:3-management-alpine` (v4 breaks Celery 5.6). `definitions.json` must declare `"vhosts": [{"name": "/"}]` first.
- **Trailing slashes**: All Django URL patterns and all `api.js` frontend calls use trailing slashes.
- **NLP module-level init**: `LLMService()` instantiates at import time — tests must set `OPENROUTER_API_KEY` before import (`conftest.py` handles this).
- **`NER_MIN_OCCURRENCES`** defaults to 5 — set to 1 when testing `extract_entities` with small inputs.

## Conventions

- Class-based DRF views (generics), custom permissions defined inline in `views.py`.
- Explicit string FK references for cross-app models: `"library.Author"`.
- `related_name` on every FK/M2M.
- Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`.
