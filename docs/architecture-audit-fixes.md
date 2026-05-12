# Architecture Audit Fixes — 2026-05-12 — COMPLETED

## Code Changes (8) — DONE ✅

| # | Discrepancy | Action | Status |
|---|-------------|--------|--------|
| 1 | genres JSONField → M2M | New Genre model, BookGenre through table, migration, serializer, views, URLs | ✅ Done |
| 2 | CI/CD missing | `.github/workflows/ci.yml`: ruff lint, Django tests, Docker build, push GHCR, deploy (commented out) | ✅ Done |
| 3 | Caddy nlp-service | Removed 4 dead routing rules | ✅ Done |
| 4 | HTTPS missing | Added `tls internal` to Caddyfile | ✅ Done |
| 5 | ARCHITECTURE.md: Django 5 | Updated to Django 6 | ✅ Done |
| 9 | restart: unless-stopped | Added to django, celery-ner, celery-llm (dev); celery-ner, celery-llm, rabbitmq, flower (prod) | ✅ Done |
| 10 | .dockerignore root | Created with standard ignores | ✅ Done |
| 12 | Makefile misleading output | Fixed nlp-service → removed, added flower port info | ✅ Done |

## Doc Changes — ARCHITECTURE.md (5) — DONE ✅

| # | Discrepancy | Action | Status |
|---|-------------|--------|--------|
| 6 | Pinia → reactive | Fixed all 4 occurrences | ✅ Done |
| 7 | UserBook → ShelfEntry | Fixed section title and description | ✅ Done |
| 8 | cover/okładka | Removed from Book description | ✅ Done |
| 11 | BookCharacters global | Added note: "nie filtrowane per książka" | ✅ Done |
| 15 | Serie missing | Added to DB schema diagram | ✅ Done |

## New Features (3) — DONE ✅

| # | Discrepancy | Action | Status |
|---|-------------|--------|--------|
| 16 | Frontend tests | Vitest + jsdom, 12/12 tests passing | ✅ Done |
| 17 | DaisyUI only light | Added `dark` theme | ✅ Done |
| 18 | No shared components | AlertMessage, LoadingSpinner, BookCard — extracted from 7 views | ✅ Done |

## Cleanup (3) — DONE ✅

| # | Discrepancy | Action | Status |
|---|-------------|--------|--------|
| 13 | infra/.env.example stale | Deleted (Java/Spring references) | ✅ Done |
| 14 | dead_letter TTL | Added `x-message-ttl: 604800000` (7 days) | ✅ Done |

## Verification

```
Django check:      0 issues
Frontend build:    42 modules, 1.63s ✅
Frontend tests:    2 files, 12/12 passed ✅
Docker compose:    dev config valid, prod config valid ✅
```
