# Spec — #85 Remove old Django domain apps

> Issue: #85 · Milestone: M1 Cleanup + UI shell · Branch: `chore/85-remove-domain-apps` (from `dev`) · Context: ADR-004

## Goal

Delete the reading-tracker domain from the backend. What remains: `users` (auth, account, settings, avatar, public profile, user list, data export) + `config` (settings, Celery wiring, pagination).

## Decisions (user, 2026-10-03)

| # | Topic | Decision |
|---|-------|----------|
| 1 | `/api/users/me/stats/` | Delete endpoint, `users/stats.py`, stats serializers, tests |
| 2 | `/api/users/me/export/` | Keep endpoint; ZIP holds only `user.json` + avatar (if set) + README — domain files dropped (OKF export replaces it later) |
| 3 | `UserFollow` | Delete here (model, admin, serializers, views, urls, counts on profile/list, tests) |
| 4 | Celery | Keep `config/celery.py`, `CELERY_*`, `OPENROUTER_*` settings and compose services (needed by the Agent) |
| 5 | `infra/scripts/seed.py` | Delete |

## Scope

### Delete entirely
- `backend-django/{books,library,ratings,shelf,reviews,feed,characters}/` (incl. migrations, tasks, management commands, tests)
- `backend-django/users/stats.py`, `users/tests/test_stats.py`
- `backend-django/users/selectors.py` (`public_owner_or_404` — only used by shelf/reviews)
- `infra/scripts/seed.py`

### Edit
- `config/settings/base.py`: drop 7 apps from `INSTALLED_APPS`; drop `character_generate` throttle; drop Google Books settings block. Keep Celery + OpenRouter.
- `config/urls.py`: drop the domain imports and routes; keep admin, auth, users, u, schema, docs.
- `users/models.py`: delete `UserFollow`. Edit `users/migrations/0001_initial.py` in place and delete follow-only migrations 0005/0006/0010 (repoint 0007 → 0004) — reset, no new migration; dev DB gets recreated.
- `users/{admin,serializers,views,urls/*}.py`: delete follow endpoints (`/api/u/{handle}/follow|followers|following/`), `FollowSerializer`, `FollowUserSerializer`, `followers_count`/`following_count`/`is_following` fields and annotations; delete `MyStatsView` + route + stats serializers. `UserListView` ordering: `created_at`, `handle` only (default `-created_at`).
- `users/exporters.py`: only `user.json` + avatar + README listing them.
- `users/tests/*`: remove follow/stats/domain cases; `test_data_export` asserts the ZIP has exactly `user.json` + README (no avatar set).
- `config/tests/test_prod_settings.py`: remove references to deleted apps/settings only.
- `docs/api/openapi.yml`: regenerate (`make regenerate-openapi`).
- `infra/.env.example`: drop Google Books and `THROTTLE_CHARACTER_GENERATE`; reword OpenRouter/Celery comments (Agent, not M13 characters).
- `CLAUDE.md`: apps list in Layout → `users, config`; drop Seed line and `seed` from `infra/scripts`.
- `docs/ARCHITECTURE.md`: no change (already describes target state).

### Out of scope
- New wiki models, Agent, OKF export.
- Removing `users` list endpoint or public profile (they stay; profile body will be redesigned later).
- Celery/Redis containers (stay).

## Done when

1. `grep -rnE "\b(books|library|ratings|shelf|reviews|feed|characters)\b\.(models|views|urls|tasks)|UserFollow|follower_set|build_user_stats|seed\.py" backend-django infra .github Makefile CLAUDE.md` → no hits.
2. `uv run python manage.py check` OK, `makemigrations --check --dry-run` → no changes.
3. `make verify` green (ruff + pytest + OpenAPI snapshot test; host → dev DB on :5432, needs `infra/.env`).
4. CI green on the PR to `dev`.

## Risks

- Editing `users/0001_initial.py` breaks existing dev DBs → fix with `docker compose down -v` or `manage.py flush` + drop old tables; acceptable per "reset DB instead of migrations" rule. Prod has no deploy yet.
- `token_blacklist` and `auth` migrations are untouched, so no cross-app migration deps break.
