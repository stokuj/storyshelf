## Why

Spring Boot backend reaches end of life for this project — 2-language architecture
(Java + Python) with separate Kafka consumers in each, manual offset management,
and limited admin tooling. Consolidate on Python with Django's batteries-included
approach: built-in admin, one language for backend + NLP, simpler messaging.

## What

- Replaced Spring Boot with Django + DRF (6 apps, 69 Python files)
- Swapped Kafka for RabbitMQ + Celery (analysis pipeline now uses HTTP callbacks)
- Migrated from session auth to JWT (simplejwt) — frontend api.js updated
- Django Admin replaces Vue admin views (Books, Authors, Series)
- Removed Kafka from NLP service — producer replaced with HTTP POST to Django
- Seed data script (20 books, 17 authors, 57 tags) at `infra/scripts/seed.py`
- 20+ bug fixes discovered during dev-up testing (.dockerignore, RabbitMQ version,
  volume mounts, healthcheck IPv6, pagination, camelCase, F5 auth restore)

## How

Architecture decision: HTTP callbacks instead of a message broker for the analysis
pipeline. Celery tasks POST to NLP, NLP POSTs results back to Django at
`/api/internal/*` (Docker-network only, IP-whitelisted middleware).

DRF field naming uses `source=` mapping for camelCase compatibility with the
existing Vue frontend. Pagination disabled on all list endpoints consumed by
frontend views (flat arrays expected).

## Testing

- [x] `make dev-up` — all 7 containers healthy (django, celery-worker, frontend, NLP, rabbitmq, redis, db)
- [x] Django `manage.py check` — 0 issues
- [x] NLP `pytest` — 40/40 unit tests pass
- [x] Frontend `npm run build` — passes
- [x] API smoke test — register, login, JWT refresh, books list, book detail, shelf, profile
- [x] Django Admin — accessible at `/admin/`, all models registered
- [x] Seed data — 20 books, 17 authors, 57 tags, idempotent

## Rollback

Switch compose back to `infra/compose/docker-compose.dev.yml` from before this PR.
No data migration needed (fresh start DB).

## Risk

Low — isolated to backend infra, zero NLP service logic changes (only removed Kafka
consumer, replaced producer with HTTP callbacks), frontend changes limited to
api.js JWT interceptors and 3 removed admin views.
