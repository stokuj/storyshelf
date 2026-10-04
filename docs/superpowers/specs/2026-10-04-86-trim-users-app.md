# Spec — #86 Trim users app to auth and profile

> Issue: #86 · Milestone: M1 Cleanup + UI shell · Branch: `chore/86-trim-users-app` (from `dev`) · Context: ADR-004

## Goal

Remove the two tracker-era endpoints the wiki does not use. What remains in `users`: auth (`/api/auth/`), account (`/api/users/me/` + password, email, avatar, settings) and the public profile (`/api/u/{handle}/`).

## Decisions (user, 2026-10-04)

| # | Topic | Decision |
|---|-------|----------|
| 1 | Profile "about" / "is public" | Keep `User.bio` and `User.profile_public` as the Profile's fields. No `Profile` model, no rename, no migration. |
| 2 | `GET /api/users/` (`UserListView`) | Delete. The wiki is private and has no people discovery. |
| 3 | `GET /api/users/me/export/` (`DataExportView`) | Delete with `users/exporters.py`. The OKF wiki export (M2) replaces it. |
| 4 | Orphans | Delete `UserListSerializer` and the `user_data_export` throttle scope. Keep `config/pagination.py` (global `DEFAULT_PAGINATION_CLASS`). |

## Scope

### Delete entirely
- `backend-django/users/exporters.py`
- `backend-django/users/tests/test_user_list.py`, `users/tests/test_data_export.py`

### Edit
- `users/views.py`: delete `DataExportView`, `UserListView`; drop imports they leave unused (`date`, `HttpResponse`, `filters`, `StandardPagination`, `UserListSerializer`).
- `users/urls/users.py`: drop `path("", ...)` and `path("me/export/", ...)` and their imports.
- `users/serializers.py`: delete `UserListSerializer`.
- `config/settings/base.py`: drop `"user_data_export": "3/day"`.
- `docs/api/openapi.yml`: regenerate (`make regenerate-openapi`).

### Out of scope
- Favourites, OKF wiki export (M2).
- Renaming `bio`/`profile_public` or a separate `Profile` model.
- `docs/ARCHITECTURE.md` (describes the target model; `Profile (about, is_public)` maps onto `User.bio`/`User.profile_public` for now).
- Historical spec of #85 (mentions the export; left as a record).

## Done when

1. `GET /api/users/` and `GET /api/users/me/export/` return 404 (covered by a test).
2. `git grep -nE "UserListView|UserListSerializer|DataExportView|exporters|user_data_export" -- backend-django docs/api` → no hits.
3. `uv run ruff check .` and `DJANGO_ENV=dev uv run python manage.py test` pass; `make verify` green (incl. OpenAPI snapshot test).
4. CI green on the PR to `dev`.

## Risks

- Frontend (`frontend/`) has no calls to these endpoints yet → nothing to update there.
