# M10 Audit / Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the consistency/dead-code findings from the M10 audit and sync documentation to the post-M6–M9 state — no new features.

**Architecture:** Six independent, individually-testable changes: drop an unused API field, consolidate the follow endpoints under the `/api/u/` prefix, link two "dead-end" UI elements (review author → profile, book genres → filtered discover), and refresh `ARCHITECTURE.md` / `ROADMAP.md`.

**Tech Stack:** Django 6 + DRF + drf-spectacular (backend), SvelteKit 2 + Svelte 5 + Tailwind v4 (frontend).

**Backend test command:** the dockerized dev DB requires an explicit `DATABASE_URL`. Run all backend tests from `backend-django/` as:
```bash
DJANGO_ENV=dev DATABASE_URL='postgres://postgres:CHANGE_ME@localhost:5432/booksdb' uv run python manage.py test <path> -v 1
```
OpenAPI regen: `make regenerate-openapi` (from repo root).

---

## File Structure

| File | Change | Task |
|------|--------|------|
| `backend-django/users/stats.py` | Remove `total_books` from `totals` | 1 |
| `backend-django/users/serializers.py` | Remove `total_books` from `_StatsTotalsSerializer` | 1 |
| `backend-django/users/tests/test_stats.py` | Drop `total_books` assertions | 1 |
| `backend-django/users/urls/public.py` | Add follow routes (now under `/api/u/`) | 2 |
| `backend-django/users/urls/users.py` | Remove follow routes + unused imports | 2 |
| `backend-django/users/tests/test_users.py` | Update follow URLs to `/api/u/…` | 2 |
| `svelte-frontend/src/lib/api/follow.ts` | Point follow calls at `/u/…` | 2 |
| `docs/api/openapi.yml` | Regenerated (Tasks 1 & 2) | 1, 2 |
| `svelte-frontend/src/lib/components/review/ReviewCard.svelte` | Link author → `/u/{handle}` | 3 |
| `svelte-frontend/src/lib/components/book/BookHeader.svelte` | Link genre → `/discover?genre=` | 4 |
| `docs/ARCHITECTURE.md` | Sync API surface + apps | 5 |
| `docs/ROADMAP.md` | M9 → done, M10 active | 6 |

---

## Task 1: Drop unused `total_books` from stats

`total_books` is emitted by the API but never rendered anywhere on the frontend (it exists only in the TS type). Remove it end to end.

**Files:**
- Modify: `backend-django/users/stats.py`
- Modify: `backend-django/users/serializers.py`
- Modify: `backend-django/users/tests/test_stats.py`
- Modify: `svelte-frontend/src/lib/api/stats.ts`
- Modify (generated): `docs/api/openapi.yml`

- [ ] **Step 1: Update the failing tests first (remove the assertions)**

In `backend-django/users/tests/test_stats.py`, delete these two assertion lines:
- line ~50: `self.assertEqual(stats["totals"]["total_books"], 3)`
- line ~108: `self.assertEqual(stats["totals"]["total_books"], 0)`

- [ ] **Step 2: Run the stats tests to confirm they still pass with assertions removed but field still present**

```bash
cd backend-django && DJANGO_ENV=dev DATABASE_URL='postgres://postgres:CHANGE_ME@localhost:5432/booksdb' uv run python manage.py test users.tests.test_stats -v 1
```
Expected: PASS (the field is still emitted; we only removed assertions).

- [ ] **Step 3: Remove the field from the aggregation**

In `backend-django/users/stats.py`, change the `totals` dict (it currently reads):
```python
    totals = {
        "total_books": entries.count(),
        "pages_read": pages_read,
        "avg_rating_given": avg_rating_given,
    }
```
to:
```python
    totals = {
        "pages_read": pages_read,
        "avg_rating_given": avg_rating_given,
    }
```

- [ ] **Step 4: Remove the field from the serializer**

In `backend-django/users/serializers.py`, in `_StatsTotalsSerializer` (around line 244), delete the line:
```python
    total_books = serializers.IntegerField()
```
so the class becomes:
```python
class _StatsTotalsSerializer(serializers.Serializer):
    pages_read = serializers.IntegerField()
    avg_rating_given = serializers.FloatField(allow_null=True)
```

- [ ] **Step 5: Remove the field from the frontend type**

In `svelte-frontend/src/lib/api/stats.ts`, change:
```ts
	totals: { total_books: number; pages_read: number; avg_rating_given: number | null };
```
to:
```ts
	totals: { pages_read: number; avg_rating_given: number | null };
```

- [ ] **Step 6: Run backend stats tests + frontend check**

```bash
cd backend-django && DJANGO_ENV=dev DATABASE_URL='postgres://postgres:CHANGE_ME@localhost:5432/booksdb' uv run python manage.py test users.tests.test_stats -v 1
```
Expected: PASS.
```bash
cd svelte-frontend && npm run check
```
Expected: 0 errors (the `/stats` page never referenced `total_books`).

- [ ] **Step 7: Regenerate OpenAPI + contract test**

```bash
make regenerate-openapi
cd backend-django && DJANGO_ENV=dev DATABASE_URL='postgres://postgres:CHANGE_ME@localhost:5432/booksdb' uv run python manage.py test config.tests.test_openapi_schema -v 1
```
Expected: snapshot diff drops `total_books` from the `_StatsTotals` schema; contract test PASS.

- [ ] **Step 8: Commit**

```bash
git add backend-django/users/stats.py backend-django/users/serializers.py backend-django/users/tests/test_stats.py svelte-frontend/src/lib/api/stats.ts docs/api/openapi.yml
git commit -m "refactor: drop unused total_books from stats"
```

---

## Task 2: Consolidate follow endpoints under `/api/u/`

Move `follow` / `followers` / `following` from `/api/users/{handle}/…` to `/api/u/{handle}/…` so they match the public profile (`/api/u/{handle}/`) and shelves (`/api/u/{handle}/shelves/`). Views and permissions are unchanged — only the URLconf and callers move.

**Files:**
- Modify: `backend-django/users/urls/public.py`
- Modify: `backend-django/users/urls/users.py`
- Modify: `backend-django/users/tests/test_users.py`
- Modify: `svelte-frontend/src/lib/api/follow.ts`
- Modify (generated): `docs/api/openapi.yml`

- [ ] **Step 1: Update the failing tests first (point them at the new URLs)**

The follow tests in `backend-django/users/tests/test_users.py` use 11 `/api/users/<handle>/{follow,followers,following}/` URLs. Rewrite only those (leave `/api/users/me/…` untouched) with:
```bash
cd backend-django && sed -i -E 's#/api/users/([^/"]+)/(follow|followers|following)/#/api/u/\1/\2/#g' users/tests/test_users.py
```
Verify the 11 occurrences changed and nothing else:
```bash
grep -n "/api/u/.*/follow\|/api/u/.*/followers\|/api/u/.*/following\|/api/users/" users/tests/test_users.py
```
Expected: follow URLs now `/api/u/…`; any remaining `/api/users/` lines are `me/` only (none in this file's follow tests).

- [ ] **Step 2: Run the follow tests to confirm they now FAIL (routes not moved yet)**

```bash
cd backend-django && DJANGO_ENV=dev DATABASE_URL='postgres://postgres:CHANGE_ME@localhost:5432/booksdb' uv run python manage.py test users.tests.test_users -v 1
```
Expected: FAIL (follow tests hit `/api/u/…` which 404s until Step 3–4).

- [ ] **Step 3: Add the follow routes to the public URLconf**

Replace the entire contents of `backend-django/users/urls/public.py` with:
```python
from django.urls import path

from users.views import FollowListView, UserFollowView, UserProfileView

urlpatterns = [
    path("<str:handle>/follow/", UserFollowView.as_view()),
    path("<str:handle>/followers/", FollowListView.as_view(follower_view=True)),
    path("<str:handle>/following/", FollowListView.as_view(follower_view=False)),
    path("<str:handle>/", UserProfileView.as_view()),
]
```

- [ ] **Step 4: Remove the follow routes (and now-unused imports) from the `users` URLconf**

Replace the entire contents of `backend-django/users/urls/users.py` with:
```python
from django.urls import path

from users.views import (
    AvatarUploadView,
    DataExportView,
    EmailChangeView,
    MyStatsView,
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
    path("me/export/", DataExportView.as_view()),
    path("me/stats/", MyStatsView.as_view()),
]
```

- [ ] **Step 5: Run the follow tests to confirm they pass**

```bash
cd backend-django && DJANGO_ENV=dev DATABASE_URL='postgres://postgres:CHANGE_ME@localhost:5432/booksdb' uv run python manage.py test users.tests.test_users -v 1
```
Expected: PASS (routes resolve at the new prefix; the public profile route still works because `<handle>/follow/` etc. are more specific than `<handle>/`).

- [ ] **Step 6: Update the frontend follow client**

Replace the contents of `svelte-frontend/src/lib/api/follow.ts` with:
```ts
import { apiFetch } from './_client';
import type { FollowUser } from '$lib/types/follow';

export function followUser(fetchFn: typeof fetch, handle: string) {
	return apiFetch<{ follower_handle: string; following_handle: string }>(
		fetchFn,
		`/u/${handle}/follow/`,
		{ method: 'POST' }
	);
}

export function unfollowUser(fetchFn: typeof fetch, handle: string) {
	return apiFetch<null>(fetchFn, `/u/${handle}/follow/`, { method: 'DELETE' });
}

export function fetchFollowers(fetchFn: typeof fetch, handle: string, isServerSide = false) {
	return apiFetch<FollowUser[]>(fetchFn, `/u/${handle}/followers/`, undefined, isServerSide);
}

export function fetchFollowing(fetchFn: typeof fetch, handle: string, isServerSide = false) {
	return apiFetch<FollowUser[]>(fetchFn, `/u/${handle}/following/`, undefined, isServerSide);
}
```

- [ ] **Step 7: Frontend check + lint**

```bash
cd svelte-frontend && npm run check && npm run lint
```
Expected: 0 errors, lint clean.

- [ ] **Step 8: Regenerate OpenAPI + contract test + ruff**

```bash
make regenerate-openapi
cd backend-django && DJANGO_ENV=dev DATABASE_URL='postgres://postgres:CHANGE_ME@localhost:5432/booksdb' uv run python manage.py test config.tests.test_openapi_schema -v 1
uv run ruff check .
```
Expected: snapshot moves the three follow paths from `/api/users/{handle}/…` to `/api/u/{handle}/…`; contract test PASS; ruff clean.

- [ ] **Step 9: Commit**

```bash
git add backend-django/users/urls/public.py backend-django/users/urls/users.py backend-django/users/tests/test_users.py svelte-frontend/src/lib/api/follow.ts docs/api/openapi.yml
git commit -m "refactor: move follow endpoints to /api/u"
```

---

## Task 3: Link review author to their profile

`ReviewCard` shows the author name as plain text though `review.author.handle` is available. Wrap it in a profile link.

**Files:**
- Modify: `svelte-frontend/src/lib/components/review/ReviewCard.svelte`

- [ ] **Step 1: Make the author name a link**

In `svelte-frontend/src/lib/components/review/ReviewCard.svelte`, replace:
```svelte
		<span class="font-medium">{review.author.display_name || `@${review.author.handle}`}</span>
```
with:
```svelte
		<a href="/u/{review.author.handle}" class="font-medium hover:text-accent transition-colors">
			{review.author.display_name || `@${review.author.handle}`}
		</a>
```

- [ ] **Step 2: Type-check + lint**

```bash
cd svelte-frontend && npm run check && npm run lint
```
Expected: 0 errors, lint clean.

- [ ] **Step 3: Commit**

```bash
git add svelte-frontend/src/lib/components/review/ReviewCard.svelte
git commit -m "feat: link review author to profile"
```

---

## Task 4: Link book genres to filtered discover

In `BookHeader`, authors link to `/discover?author=…` but genres are plain `<Badge>`s. `/discover` already reads `?genre=`. Make each genre badge a link, consistent with authors.

**Files:**
- Modify: `svelte-frontend/src/lib/components/book/BookHeader.svelte`

- [ ] **Step 1: Wrap each genre badge in a discover link**

In `svelte-frontend/src/lib/components/book/BookHeader.svelte`, replace:
```svelte
		{#each book.genres as genre (genre)}
			<Badge variant="secondary">{genre}</Badge>
		{/each}
```
with:
```svelte
		{#each book.genres as genre (genre)}
			<a href="/discover?genre={encodeURIComponent(genre)}">
				<Badge variant="secondary" class="hover:bg-accent/15 transition-colors">{genre}</Badge>
			</a>
		{/each}
```

- [ ] **Step 2: Type-check + lint**

```bash
cd svelte-frontend && npm run check && npm run lint
```
Expected: 0 errors, lint clean.

- [ ] **Step 3: Commit**

```bash
git add svelte-frontend/src/lib/components/book/BookHeader.svelte
git commit -m "feat: link book genres to discover filter"
```

---

## Task 5: Sync `ARCHITECTURE.md`

Update the doc to reflect M6 (follow) + M9 (stats). Exact edits below.

**Files:**
- Modify: `docs/ARCHITECTURE.md`

- [ ] **Step 1: Update the `users/` app row**

Change the line (around line 36):
```
| `users/`  | Custom User (email, handle, display_name, bio, avatar_url, profile_public), auth, profil, follow, data export |
```
to:
```
| `users/`  | Custom User (email, handle, display_name, bio, avatar_url, profile_public), auth, profil, follow, data export, reading stats (`stats.py::build_user_stats`) |
```

- [ ] **Step 2: Update the API surface heading and `me/` line**

Change the heading (around line 60) from:
```
## API surface (M1–M5)
```
to:
```
## API surface (M1–M9; M7 admin-import odłożone)
```
Change the `me/` line (around line 64) from:
```
/api/users/me/        profil, settings (profile_public), email, password, avatar, export
```
to:
```
/api/users/me/        profil, settings (profile_public), email, password, avatar, export, stats
```

- [ ] **Step 3: Add the follow endpoints under the public-profile lines**

After the line (around line 66):
```
/api/u/{handle}/shelves/   publiczne custom półki (bramkowane profile_public)
```
insert:
```
/api/u/{handle}/follow/        follow/unfollow (auth)
/api/u/{handle}/followers/, /api/u/{handle}/following/   listy obserwujących/obserwowanych
```

- [ ] **Step 4: Verify no dangling references and the file reads correctly**

```bash
cd /home/dv6/GitHub/storyshelf && grep -n "GOAL.md\|/api/users/{handle}/follow\|M1–M5" docs/ARCHITECTURE.md
```
Expected: no output (no GOAL.md ref, no old follow prefix, heading no longer says M1–M5).

- [ ] **Step 5: Commit**

```bash
git add docs/ARCHITECTURE.md
git commit -m "docs: sync ARCHITECTURE for M6-M9"
```

---

## Task 6: Sync `ROADMAP.md`

Move M9 to "Zrobione" and set "Aktualny krok" to M10 in progress.

**Files:**
- Modify: `docs/ROADMAP.md`

- [ ] **Step 1: Update "Aktualny krok"**

In `docs/ROADMAP.md`, change the "Bieżący branch" / "ZADANIE" block under `## Aktualny krok` so it reads (replace the current branch line and task line):
```
**Bieżący branch:** `chore/m10-audit-cleanup` (M9 zmergowane przez PR #72; M10 w toku).

**ZADANIE:** **M10 — Audyt / fix / cleanup** (ostatni milestone przed wdrożeniem). Po M10: wdrożenie produkcyjne.
```
(Keep the existing "M8 zamknięte" / "M7 odłożone" notes below it.)

- [ ] **Step 2: Add M9 to the "Zrobione" table**

In the `## Zrobione` table, after the M8 row, add:
```
| M9 Statystyki czytania | `GET /api/users/me/stats/` (auth, own-only) + `users/stats.py::build_user_stats` (status counts, książki/rok z `finish_date`, rozkład ocen, time-on-shelf); auto-set `ShelfEntry.finish_date` na przejściu do READ; frontend `/stats` + ręczny `BarChart` (zero deps); E2E `stats.spec.ts`; OpenAPI zregenerowany | ✅ zmergowane do main (PR #72) |
```

- [ ] **Step 3: Remove the M9 row from the "Następne" table**

In the `## Następne` table, delete the row beginning with `| **M9 — Statystyki czytania** (B1) — AKTYWNE |`. (M10 stays in the table or can be marked AKTYWNE — leave M10 row as-is.)

- [ ] **Step 4: Sanity check**

```bash
cd /home/dv6/GitHub/storyshelf && grep -n "M9 — Statystyki\|chore/m10-audit-cleanup\|PR #72" docs/ROADMAP.md
```
Expected: M9 appears in "Zrobione", current branch is `chore/m10-audit-cleanup`, M9 no longer in "Następne" as AKTYWNE.

- [ ] **Step 5: Commit**

```bash
git add docs/ROADMAP.md
git commit -m "docs: roadmap M9 done, M10 active"
```

---

## Task 7: Final verification

- [ ] **Step 1: Backend full suite + ruff**

```bash
cd backend-django && DJANGO_ENV=dev DATABASE_URL='postgres://postgres:CHANGE_ME@localhost:5432/booksdb' uv run python manage.py test -v 1
uv run ruff check .
```
Expected: all green, ruff clean.

- [ ] **Step 2: Frontend check + lint**

```bash
cd svelte-frontend && npm run check && npm run lint
```
Expected: 0 errors, lint clean.

- [ ] **Step 3: E2E follow still passes (URLs moved)**

With the dev stack up and the register throttle relaxed (or after `docker restart storyshelf-django`):
```bash
cd svelte-frontend && npx playwright test follow.spec.ts
```
Expected: pass (the spec calls `follow.ts`, which now targets `/api/u/…`).

- [ ] **Step 4: Smoke the two new links**

With the dev stack up: open a book detail with reviews → click a review author → lands on `/u/{handle}`; click a genre badge → lands on `/discover?genre=…` filtered list.

- [ ] **Step 5: Done** — proceed to `/finishing-a-development-branch`.

---

## Self-Review notes

- **Spec coverage:** #1 ReviewCard link → Task 3. #2 BookHeader genre link → Task 4. #3 follow prefix consolidation → Task 2. #4 remove total_books → Task 1. #5 ARCHITECTURE sync → Task 5. #6 ROADMAP sync → Task 6. Final verification + E2E follow → Task 7.
- **Type consistency:** `total_books` removed in the same names across `stats.py` (dict key), `_StatsTotalsSerializer` (field), and `stats.ts` (`UserStats.totals`). Follow paths use the identical `/u/${handle}/{follow,followers,following}/` form in `public.py` and `follow.ts`.
- **Out of scope (per spec):** backend NITs (stale finish_date, time-on-shelf basis), `/users` list, homepage, deployment config, `/api/users/me/*`.
- **Note:** the M10 spec/plan removal commit ("docs: remove M10 spec + plan") is part of `/finishing-a-development-branch`, not this plan.
