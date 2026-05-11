# Django API Audit — Design

**Date:** 2026-05-11  
**Branch:** `feature/django-audit`  
**Scope:** Full audit of Django REST API (37 endpoints across 6 apps)

## Goal

Systematically audit every Django API endpoint for correctness, security, and code
quality. Find trivial bugs and fix them. Report critical issues that require
architectural decisions.

## Approach

**App-by-app with checkpoints** — each app tested independently, bugs fixed or
documented per-app, final AUDIT.md aggregates all findings.

## Test Architecture

### Framework

Built-in `django.test.TestCase` + `rest_framework.test.APITestCase`. No pytest.

### File structure (per app, in existing `tests/`)

```
backend-django/<app>/tests/
    __init__.py
    test_auth.py          # users only — register, login, refresh, logout, me
    test_users.py         # users only — profile, settings, visibility, follow
    test_books.py         # books — CRUD, search, chapters, characters, relations
    test_views.py         # shelf, reviews, library, analysis (one file per app)
```

### Shared base helper

`backend-django/config/test_helpers.py` — mixin creating test users (USER,
MODERATOR, ADMIN) and minimal fixtures per app.

### Naming convention

`test_<method>_<scenario>_<expected_behavior>`

### Per-endpoint test coverage

- Happy path with correct HTTP status
- Response structure validation (keys, types, camelCase) vs serializer
- 401 when auth required but no token
- 403 when role insufficient
- 400 for invalid/empty body or missing required fields
- 404 for nonexistent IDs
- 409/duplicates where applicable (self-follow, already following)

## Auth Testing Strategy

### Path A: Real HTTP + JWT flow (auth endpoints only)

`RegisterView`, `LoginView`, `LogoutView`, `AuthMeView` — `force_authenticate`
cannot generate JWT tokens. Test with real HTTP requests:

register → login → extract token → use in `Authorization` header.

### Path B: `force_authenticate` (all other endpoints)

Books, shelf, reviews, library, users/profile — faster, tests view logic directly
without JWT overhead.

| App | Test file | Method |
|-----|-----------|--------|
| users | `test_auth.py` | Real JWT flow |
| users | `test_users.py` | `force_authenticate` |
| books | `test_books.py` | `force_authenticate` |
| shelf | `test_views.py` | `force_authenticate` |
| reviews | `test_views.py` | `force_authenticate` |
| library | `test_views.py` | `force_authenticate` |
| analysis | `test_views.py` | `force_authenticate` + override `REMOTE_ADDR` |

### Internal middleware

`analysis/middleware.py` blocks non-Docker IPs (requires 172.16.0.0/12). Tests
set `REMOTE_ADDR` to `172.18.0.1` instead of mocking — tests the real middleware.

## Fix Policy

| Category | Action |
|----------|--------|
| Trivial bug, clear fix | Fix in code + add test |
| Missing validation, edge case | Fix in code + add test |
| Missing `select_related` / N+1 | Fix in code + add `assertNumQueries` |
| Security hole | Fix immediately + add test |
| Architectural problem | Report in AUDIT.md + create issue |
| Convention violation, works fine | Report in AUDIT.md as minor |

### Known bug to fix

`/books/{id}/details/` in `books/urls.py:14` is a duplicate of `/books/{id}/` —
both route to `BookDetailView`. Remove the `details/` line, verify frontend does
not use it.

## Execution Order

| # | App | Test file(s) | Endpoints | Risk |
|---|-----|-------------|-----------|------|
| 1 | users | `test_auth.py` + `test_users.py` | 11 | Auth foundation |
| 2 | books | `test_books.py` | 12 | Core functionality |
| 3 | shelf | `test_views.py` | 2 | Depends on books + users |
| 4 | reviews | `test_views.py` | 2 | Depends on books + users |
| 5 | library | `test_views.py` | 4 | Authors + Series, simple |
| 6 | analysis | `test_views.py` | 4 | Internal callbacks + middleware |

## Commit Strategy

One commit per app + tests. Final commit for AUDIT.md:

```
fix: remove duplicate /books/{id}/details/ endpoint
test: add auth endpoint tests (register, login, refresh, me)
test: add user profile, follow, visibility tests
test: add book CRUD, chapter, character, relation tests
test: add shelf CRUD tests
test: add review create/delete tests
test: add author and series CRUD tests
test: add analysis internal callback tests
docs: add AUDIT.md with audit findings
```

## Deliverables

1. Test files in each app's `tests/` directory — passing, executable
2. Bug fixes applied to source code (where fix is obvious)
3. `AUDIT.md` at repo root with:
   - Summary (endpoints tested, issues found, issues fixed)
   - Critical issues requiring architectural decisions
   - Minor issues
   - List of fixes applied

## Run Commands

```bash
cd backend-django
DJANGO_ENV=dev uv run python manage.py test users
DJANGO_ENV=dev uv run python manage.py test books
DJANGO_ENV=dev uv run python manage.py test       # all tests
```
