# Django API Audit

**Date:** 2026-05-11
**Branch:** feature/django-audit
**Tests:** 129 across 6 apps
**Result:** All passing

## Summary

| Category | Count |
|----------|-------|
| Endpoints audited | 37 |
| Tests written | 129 |
| Bugs found and fixed | 5 |
| Critical issues | 0 |
| Minor issues | 2 |

## Bugs Found and Fixed

### 1. RegisterSerializer — missing UniqueValidator on username (FIXED)

**Severity:** MEDIUM
**What:** `RegisterSerializer` declared `username` as `RegexField` explicitly,
which bypassed the model-level `unique=True` validator. A duplicate username
passed `is_valid()` and hit an unhandled `IntegrityError` at `save()` → HTTP 500.

**Fix:** Added `validators=[UniqueValidator(queryset=User.objects.all())]` to
the `username` field. Also removed unused `import re`.
**File:** `backend-django/users/serializers.py:14`

### 2. BookCreateSerializer — missing write_only=True on author_id (FIXED)

**Severity:** MEDIUM
**What:** `author_id` is consumed in `perform_create` to look up an Author and
attach it via M2M, but the field is not a `Book` model field. Without
`write_only=True`, DRF would pass it to `Book.objects.create()` causing an
unexpected keyword argument error.

**Fix:** Added `write_only=True` to the `author_id` IntegerField.
**File:** `backend-django/books/serializers.py:77`

### 3. ReviewSerializer — missing duplicate (book, user) validation (FIXED)

**Severity:** MEDIUM
**What:** A user posting a second review for the same book hit a DB
`IntegrityError` on the `(book, user)` unique constraint → HTTP 500 instead of
a clean validation error.

**Fix:** Added `validate()` method to `ReviewSerializer` checking for existing
`Review` per (book, user) and raising `ValidationError` → HTTP 400.
**File:** `backend-django/reviews/serializers.py`

### 4. Author/Series ListCreateView — missing pagination_class = None (FIXED)

**Severity:** LOW
**What:** The frontend expects flat arrays from list endpoints. `AuthorListCreateView`
and `SeriesListCreateView` had no explicit `pagination_class = None`, which would
use the DRF default `PageNumberPagination` (returning `{count, next, results}`
instead of a plain array).

**Fix:** Added `pagination_class = None` to both views.
**File:** `backend-django/library/views.py:17,28`

### 5. `/books/{id}/details/` — duplicate endpoint (FIXED)

**Severity:** LOW
**What:** `books/urls.py` had both `/<int:pk>/` and `/<int:pk>/details/` routing
to the same `BookDetailView`. The frontend used the `/details/` variant.

**Fix:** Removed the `details/` URL pattern and updated `frontend/src/api.js:79`
to use `/${bookId}/` directly.
**Files:** `backend-django/books/urls.py`, `frontend/src/api.js`

## Minor Issues (not fixed, documented for consideration)

### 1. Three near-identical permission classes across apps

**Severity:** LOW
`class IsModerator` (books/views.py:20), `class IsModeratorForDelete`
(reviews/views.py:8), and `class IsModeratorOrReadOnly` (library/views.py:6)
all have the same logic: check role in (MODERATOR, ADMIN). These could be
extracted to a shared `config/permissions.py` module.

### 2. InternalEndpointMiddleware hardcodes Docker bridge network

**Severity:** LOW
`analysis/middleware.py` checks `REMOTE_ADDR` against `172.16.0.0/12`.
On custom Docker networks or non-Docker deployments, internal endpoints would
be inaccessible. Consider making the CIDR configurable via environment variable.

### 3. UserVisibilityView reads profilePublic from query params in PATCH

**Severity:** LOW
`users/views.py:99` reads `request.query_params` instead of `request.data` in
a PATCH endpoint. This is non-standard and could surprise API consumers.
The current frontend works with this pattern.

### 4. Chapter upload triggers Celery tasks synchronously in dev

**Severity:** NOTE
`ChapterView.post()` calls `analyse_chapter.delay()` and `ner_chapter.delay()`.
In dev mode (`CELERY_TASK_ALWAYS_EAGER=True`), these run synchronously and fail
if the NLP service is not running. Production mode handles this correctly via
message broker. Tests mock these tasks with `@patch`.

## Test Statistics

| App | Tests | Endpoints covered |
|-----|-------|------------------|
| users | 41 | register, login, refresh, logout, me, profile, settings, visibility, follow, followers, following |
| books | 22 | list, create, detail, update, delete, chapters, characters, relations, search |
| library | 23 | authors CRUD, series CRUD |
| shelf | 16 | shelf list, entry CRUD |
| reviews | 14 | book reviews, review delete |
| analysis | 13 | analyse-result, ner-result, find-pairs, relations-result |
| **Total** | **129** | **37** |

## Verification

```bash
$ cd backend-django && DJANGO_ENV=dev uv run python manage.py test -v2
Ran 129 tests in 23.350s
OK
```
