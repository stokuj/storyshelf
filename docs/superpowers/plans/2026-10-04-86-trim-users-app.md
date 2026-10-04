# #86 Trim users app Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove `GET /api/users/` (people discovery) and `GET /api/users/me/export/` (tracker data export) from the `users` app.

**Architecture:** Pure deletion. Remove the two views, their routes, serializer, exporter, throttle scope and tests; pin the removal with one 404 test; regenerate the OpenAPI snapshot.

**Tech Stack:** Django 6, DRF, drf-spectacular, `uv`, ruff.

**Spec:** `docs/superpowers/specs/2026-10-04-86-trim-users-app.md`

## Global Constraints

- Branch `chore/86-trim-users-app` from `dev`; PR → `dev`.
- No model changes, no migrations (`bio`, `profile_public` stay on `User`).
- Keep `config/pagination.py` (global `DEFAULT_PAGINATION_CLASS`).
- Commits: conventional, title ≤ 50 chars, no `Co-Authored-By`.
- Commands run from `backend-django/`; tests need `DJANGO_ENV=dev` and a live dev DB (`make dev-up`).

## Review Focus

1. Remaining `me/*` routes (`me/`, `me/password/`, `me/email/`, `me/avatar/`, `me/settings/`) still resolve → covered by existing tests in `users/tests/` staying green.
2. Public profile `/api/u/{handle}/` unaffected → `test_public_profile.py`, `test_users.py` stay green.
3. OpenAPI snapshot no longer lists the two paths → `config.tests.test_openapi_schema` green after regeneration.

---

### Task 1: Remove list and export endpoints

**Files:**
- Delete: `backend-django/users/exporters.py`, `backend-django/users/tests/test_user_list.py`, `backend-django/users/tests/test_data_export.py`
- Modify: `backend-django/users/views.py` (imports lines 2, 6, 7, 16, 26; `DataExportView` ~252–262; `UserListView` ~284–295)
- Modify: `backend-django/users/urls/users.py`
- Modify: `backend-django/users/serializers.py` (`UserListSerializer` ~127–137)
- Modify: `backend-django/config/settings/base.py:104`
- Test: `backend-django/users/tests/test_users.py`

**Interfaces:**
- Consumes: `config.test_helpers.AuthTestHelper` (`cls.user`).
- Produces: nothing new.

- [ ] **Step 1: Write the failing test** — append to `users/tests/test_users.py`:

```python
class RemovedEndpointsTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()

    def test_user_list_returns_404(self):
        resp = self.client.get("/api/users/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_data_export_returns_404(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get("/api/users/me/export/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
```

- [ ] **Step 2: Run it, expect FAIL**

Run: `DJANGO_ENV=dev uv run python manage.py test users.tests.test_users.RemovedEndpointsTest`
Expected: 2 failures (list → 200, export → 405).

- [ ] **Step 3: Delete files**

```bash
git rm users/exporters.py users/tests/test_user_list.py users/tests/test_data_export.py
```

- [ ] **Step 4: `users/urls/users.py`** — final content:

```python
from django.urls import path

from users.views import (
    AvatarUploadView,
    EmailChangeView,
    PasswordChangeView,
    UserMeView,
    UserSettingsView,
)

urlpatterns = [
    path("me/", UserMeView.as_view()),
    path("me/password/", PasswordChangeView.as_view()),
    path("me/email/", EmailChangeView.as_view()),
    path("me/avatar/", AvatarUploadView.as_view()),
    path("me/settings/", UserSettingsView.as_view()),
]
```

- [ ] **Step 5: `users/views.py`** — delete classes `DataExportView` and `UserListView` entirely, then remove the imports they leave unused: `from datetime import date`, `HttpResponse` (keep `Http404`), `filters` from `rest_framework`, `from config.pagination import StandardPagination`, `UserListSerializer`. Confirm with `uv run ruff check users/views.py` (F401 must report nothing).

- [ ] **Step 6: `users/serializers.py`** — delete class `UserListSerializer`. `config/settings/base.py` — delete the line `"user_data_export": "3/day",`.

- [ ] **Step 7: Run tests and lint, expect PASS**

```bash
uv run ruff check .
DJANGO_ENV=dev uv run python manage.py test users
```

Expected: ruff clean; all `users` tests pass incl. `RemovedEndpointsTest`.

- [ ] **Step 8: Commit**

```bash
git add -A users config/settings/base.py
git commit -m "chore: remove user list and data export"
```

### Task 2: Regenerate OpenAPI and verify

**Files:**
- Modify: `docs/api/openapi.yml` (generated)

- [ ] **Step 1: Regenerate**

Run (repo root): `make regenerate-openapi`
Expected: `docs/api/openapi.yml` loses `/api/users/:` and `/api/users/me/export/:` paths and the `UserList`/`PaginatedUserListList` schemas.

- [ ] **Step 2: Grep for leftovers**

Run (repo root): `git grep -nE "UserListView|UserListSerializer|DataExportView|exporters|user_data_export" -- backend-django docs/api`
Expected: no output.

- [ ] **Step 3: Full verification**

Run (repo root): `make verify`
Expected: green (ruff + backend tests + OpenAPI snapshot test + frontend checks).

- [ ] **Step 4: Commit**

```bash
git add docs/api/openapi.yml
git commit -m "chore: regenerate OpenAPI snapshot"
```
