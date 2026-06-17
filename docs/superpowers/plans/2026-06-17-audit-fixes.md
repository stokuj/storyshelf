# Audit Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the 23 actionable findings from the 2026-06-16 audit (spec: `docs/superpowers/specs/2026-06-17-audit-fixes-design.md`) on branch `fix/audit-2026-06`, one commit per task.

**Architecture:** Surgical changes grouped A–F (prod-config, auth/SSR, frontend, backend, tests/CI, docs). TDD where a behavioural test is meaningful; config/docs changes are verified by lint/check/build. The 6 "no-change" findings stay won't-fix (documented in the spec); the email-change finding gets a clarifying comment only.

**Tech Stack:** Django 6 + DRF (`uv`, `pytest`, `ruff`), SvelteKit 2 + Svelte 5 (`npm`, `svelte-check`, Playwright), Docker Compose + Caddy, GitHub Actions.

**Conventions:**
- Backend tests: `DJANGO_ENV=dev uv run python -m pytest <path>` from `backend-django/` (needs live dev-DB: `make dev-up`, or CI postgres).
- Commit titles ≤50 chars, conventional prefixes, **no** `Co-Authored-By`.
- Run `uv run ruff check .` (backend) / `npm run check && npm run lint` (frontend) before each commit that touches that side.

---

## Group A — Prod deployment hardening

### Task 1: Caddy gets DOMAIN / ACME email (A1, high)

**Files:**
- Modify: `infra/compose/docker-compose.prod.yml:76-89` (caddy service)

- [ ] **Step 1: Add env_file to the caddy service**

In the `caddy:` block, add `env_file` so Caddy's `{$DOMAIN}` / `{$CADDY_ACME_EMAIL}` substitutions resolve (mirrors `django`/`celery`/`svelte`):

```yaml
  caddy:
    image: caddy:2-alpine
    container_name: storyshelf-caddy
    env_file:
      - ../.env
    ports:
      - "80:80"
      - "443:443"
```

- [ ] **Step 2: Verify compose parses**

Run: `docker compose -f infra/compose/docker-compose.prod.yml config >/dev/null && echo OK`
Expected: `OK` (no error). The caddy service now shows `env_file`.

- [ ] **Step 3: Commit**

```bash
git add infra/compose/docker-compose.prod.yml
git commit -m "fix: pass .env to prod caddy for TLS vars"
```

### Task 2: prod ALLOWED_HOSTS includes DOMAIN (A2, high)

**Files:**
- Modify: `backend-django/config/settings/prod.py`
- Modify: `infra/.env.example:1-13`
- Test: `backend-django/config/tests/test_prod_settings.py` (create)

- [ ] **Step 1: Write the failing test**

```python
# backend-django/config/tests/test_prod_settings.py
import importlib
import os
from unittest import mock

from django.test import SimpleTestCase


class ProdAllowedHostsTests(SimpleTestCase):
    def test_domain_appended_to_allowed_hosts(self):
        env = {
            "DJANGO_ENV": "prod",
            "DJANGO_SECRET_KEY": "x" * 50,
            "DOMAIN": "storyshelf.example.com",
            "ALLOWED_HOSTS": "localhost,127.0.0.1",
            "CSRF_TRUSTED_ORIGINS": "https://storyshelf.example.com",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            from config.settings import prod

            importlib.reload(prod)
            self.assertIn("storyshelf.example.com", prod.ALLOWED_HOSTS)
```

- [ ] **Step 2: Run it, expect FAIL**

Run: `DJANGO_ENV=dev uv run python -m pytest config/tests/test_prod_settings.py -v`
Expected: FAIL (`storyshelf.example.com` not in ALLOWED_HOSTS).

- [ ] **Step 3: Append DOMAIN in prod.py**

After the imports in `backend-django/config/settings/prod.py` (the `from .base import *` pulls in `ALLOWED_HOSTS`), add:

```python
# prod.py does not set ALLOWED_HOSTS itself; fold the Caddy DOMAIN in so a
# deployer who only edits secrets still answers on the real hostname (otherwise
# DEBUG=False + localhost-only hosts => 400 DisallowedHost on every request).
_domain = os.getenv("DOMAIN")
if _domain and _domain not in ALLOWED_HOSTS:  # noqa: F405
    ALLOWED_HOSTS = [*ALLOWED_HOSTS, _domain]  # noqa: F405
```

- [ ] **Step 4: Run the test, expect PASS**

Run: `DJANGO_ENV=dev uv run python -m pytest config/tests/test_prod_settings.py -v`
Expected: PASS.

- [ ] **Step 5: Update `.env.example` so the instruction is correct**

Change the header line 3 and the ALLOWED_HOSTS line:

```
# by the prod compose env_file. Dev defaults are fine as-is; in PROD also set
# ALLOWED_HOSTS to your domain (or rely on DOMAIN being auto-added) and secrets.
```
```
ALLOWED_HOSTS=localhost,127.0.0.1   # prod: add your domain, or it's taken from DOMAIN below
```

- [ ] **Step 6: Commit**

```bash
git add backend-django/config/settings/prod.py backend-django/config/tests/test_prod_settings.py infra/.env.example
git commit -m "fix: add DOMAIN to prod ALLOWED_HOSTS"
```

---

## Group C — Frontend correctness + a11y (C1 high first)

### Task 3: Navbar search re-syncs /discover (C1, high)

**Files:**
- Modify: `svelte-frontend/src/routes/discover/+page.svelte:33-46`
- Test: `svelte-frontend/e2e/discover.spec.ts` (add one test)

- [ ] **Step 1: Add a re-seed `$effect` after the `$state` declarations**

Insert right after the `currentAuthor` declaration (line ~46), before `hasFilters`:

```svelte
	// Re-sync local state when a same-route navigation (e.g. the navbar search in
	// AppShell, which calls goto('/discover?q=...')) delivers fresh server data for
	// a DIFFERENT query than what is shown. Client-driven updates (loadBooks) set
	// currentQ etc. BEFORE the URL changes, so data already matches and this is a
	// no-op for them — only external navigation re-seeds.
	$effect(() => {
		if (
			data.initialQ !== currentQ ||
			data.initialGenre !== currentGenre ||
			data.initialSort !== currentSort ||
			data.initialAuthor !== currentAuthor
		) {
			books = data.initialBooks;
			currentPage = data.initialPage;
			total = data.initialTotal;
			currentQ = data.initialQ;
			currentGenre = data.initialGenre;
			currentSort = data.initialSort;
			currentAuthor = data.initialAuthor;
		}
	});
```

- [ ] **Step 2: Add an E2E test reproducing the bug**

Append inside the `describe('Discover page')` block in `e2e/discover.spec.ts`:

```ts
	test('navbar search updates results while already on /discover', async ({ page }) => {
		await page.goto('/discover');
		await page.waitForSelector('.grid h3');
		// The navbar search form (AppShell) is hidden below sm; set a wide viewport.
		await page.setViewportSize({ width: 1280, height: 800 });
		const navSearch = page.getByRole('searchbox', { name: 'Search books' });
		await navSearch.click();
		await navSearch.pressSequentially('Dune', { delay: 50 });
		await navSearch.press('Enter');
		await expect(page).toHaveURL(/\/discover\?q=Dune/);
		await expect(page.locator('.grid h3', { hasText: 'Dune' })).toBeVisible();
		await expect(page.locator('.grid h3')).toHaveCount(1);
	});
```

- [ ] **Step 3: Run check + the E2E test**

Run: `cd svelte-frontend && npm run check` (expect 0 errors) then with the dev stack up: `npm run test:e2e -- discover.spec.ts`
Expected: the new test PASSES (FAILS without the Step-1 effect).

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/src/routes/discover/+page.svelte svelte-frontend/e2e/discover.spec.ts
git commit -m "fix: re-sync discover state on navbar search"
```

### Task 15: Export uses POST, not GET (C2, low)

**Files:**
- Modify: `svelte-frontend/src/routes/settings/data/export/+server.ts:7`
- Modify: `svelte-frontend/src/routes/settings/data/+page.svelte:30`

- [ ] **Step 1: Change the handler from GET to POST**

In `export/+server.ts`, rename the exported handler and keep the body identical:

```ts
export const POST: RequestHandler = async ({ fetch }) => {
```

- [ ] **Step 2: Change the trigger to a form POST**

In `settings/data/+page.svelte:30`, replace the `<Button href=...>` download link with a POST form (downloads via the server endpoint):

```svelte
		<form method="POST" action="/settings/data/export" data-sveltekit-reload>
			<Button type="submit" variant="outline" size="sm">Download my data (ZIP)</Button>
		</form>
```

(Adjust the visible label/icon to match the current button text.)

- [ ] **Step 3: Verify**

Run: `cd svelte-frontend && npm run check && npm run lint`
Expected: 0 errors. Manually: clicking the button downloads the ZIP (POST in network tab).

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/src/routes/settings/data/export/+server.ts svelte-frontend/src/routes/settings/data/+page.svelte
git commit -m "fix: trigger data export via POST not GET"
```

### Task 16: aria-labels on search inputs (C3, low)

**Files:**
- Modify: `svelte-frontend/src/lib/components/discover/FilterBar.svelte:64`
- Modify: `svelte-frontend/src/routes/users/+page.svelte:79-85`

- [ ] **Step 1: Add aria-label to both inputs**

FilterBar line 64:
```svelte
		<Input class="pl-8" placeholder="Search books…" aria-label="Search books" value={query} oninput={handleSearchInput} />
```
users/+page.svelte line ~80:
```svelte
			<input
				type="search"
				placeholder="Search people"
				aria-label="Search people"
				bind:value={search}
				oninput={onSearchInput}
				class="w-full sm:max-w-xs rounded-lg border border-rule bg-surface px-3 py-2 text-ink"
			/>
```

- [ ] **Step 2: Verify + commit**

Run: `cd svelte-frontend && npm run check && npm run lint` (expect 0 errors).
```bash
git add svelte-frontend/src/lib/components/discover/FilterBar.svelte svelte-frontend/src/routes/users/+page.svelte
git commit -m "fix: label discover and people search inputs"
```

### Task 17: Fix listbox option semantics (C4, low)

**Files:**
- Modify: `svelte-frontend/src/lib/components/discover/FilterBar.svelte:69-104,108-137`

> Keep `role="listbox"` (the E2E suite locates dropdowns via `getByRole('listbox')`); add the missing option semantics so AT announces real options.

- [ ] **Step 1: Add aria-expanded to both trigger buttons**

On the genre trigger (line 69) and sort trigger (line 109) `<button>`, add `aria-expanded={genreOpen}` / `aria-expanded={sortOpen}` and `aria-haspopup="listbox"`.

- [ ] **Step 2: Give each option `role="option"` + aria-selected**

For every option `<button>` inside both listboxes, add `role="option"` and `aria-selected`:
- Genre "All genres": `role="option"` `aria-selected={genre === ''}`
- Genre `{#each}` button: `role="option"` `aria-selected={genre === g.name}`
- Sort `{#each}` button: `role="option"` `aria-selected={sort === option.value}`

- [ ] **Step 3: Verify, including existing E2E selectors**

Run: `cd svelte-frontend && npm run check && npm run lint` (0 errors). With dev stack: `npm run test:e2e -- discover.spec.ts` — the `getByRole('listbox')` tests still pass.

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/src/lib/components/discover/FilterBar.svelte
git commit -m "fix: add option roles to discover dropdowns"
```

---

## Group B — Frontend auth / SSR

### Task 4: Remove dead SSR token-refresh (B1+B2, medium+low)

**Files:**
- Modify: `svelte-frontend/src/lib/api/_client.ts:66-80`

> The refresh cookie is path-scoped to `/api/auth/refresh/` (backend `users/cookie_auth.py`), so it is never sent on an SSR page request. The SSR `401 → attemptTokenRefresh → retry` path therefore can never authenticate; it only fired a burst of failing `/auth/refresh/` calls (one per parallel load fetch). Removing it fixes both B1 (wasted/misleading refresh) and B2 (refresh burst). Client-side refresh (the non-SSR branch) keeps working and is unchanged.

- [ ] **Step 1: Replace the isServerSide branch**

```ts
	if (isServerSide) {
		const controller = new AbortController();
		const timeoutId = setTimeout(() => controller.abort(), 10_000);
		options = { ...options, signal: controller.signal };
		const result = await fetchJson<T>(fetchFn, url, options);
		clearTimeout(timeoutId);
		// No SSR token refresh: the refresh cookie is path-scoped to
		// /api/auth/refresh/ (backend users/cookie_auth.py), so it is never sent
		// on SSR page requests — a refresh here cannot authenticate and used to
		// fire one failing /auth/refresh/ per parallel load fetch. The browser
		// refreshes client-side instead.
		return result;
	}
```

- [ ] **Step 2: Verify `attemptTokenRefresh` is still used (client branch) so no dead import**

Run: `cd svelte-frontend && npm run check && npm run lint`
Expected: 0 errors, no "unused" warning for `attemptTokenRefresh` (still called at line ~85).

- [ ] **Step 3: Commit**

```bash
git add svelte-frontend/src/lib/api/_client.ts
git commit -m "fix: drop dead SSR token-refresh burst"
```

### Task 5: Forward rotated cookies on password change (B3, low)

**Files:**
- Modify: `svelte-frontend/src/routes/settings/+page.server.ts:1-3,72-95`

> Backend `PasswordChangeView` blacklists old tokens and issues new cookies; the action currently drops them, logging the user out on next refresh. Mirror `routes/login/+page.server.ts` (which calls `forwardSetCookies`).

- [ ] **Step 1: Import the helper**

Add to the imports at the top:
```ts
import { forwardSetCookies } from '$lib/server/cookies';
```

- [ ] **Step 2: Add `cookies` to the password action and forward**

```ts
	password: async ({ request, fetch, cookies }) => {
		// ... unchanged validation + fetch ...
		if (!res.ok) return fail(res.status, { error: await apiError(res) });
		forwardSetCookies(res, cookies);
		return { success: true };
	},
```

- [ ] **Step 3: Verify + commit**

Run: `cd svelte-frontend && npm run check && npm run lint` (0 errors).
```bash
git add svelte-frontend/src/routes/settings/+page.server.ts
git commit -m "fix: forward new cookies on password change"
```

---

## Group D — Backend

### Task 10: Tighten auth_register default (D1, low)

**Files:**
- Modify: `backend-django/config/settings/base.py:106`

> Safe in CI: the e2e job overrides `THROTTLE_AUTH_REGISTER: 120/min` (ci.yml:99); pytest disables throttles entirely (dev.py:22-23).

- [ ] **Step 1: Lower the default**

```python
        "auth_register": os.getenv("THROTTLE_AUTH_REGISTER", "5/hour"),
```

- [ ] **Step 2: Verify + commit**

Run: `cd backend-django && uv run ruff check . && DJANGO_ENV=dev uv run python manage.py check`
```bash
git add backend-django/config/settings/base.py
git commit -m "fix: tighten default register throttle to 5/h"
```

### Task 11: Feed cursor keeps full boundary tie-group (D2, low)

**Files:**
- Modify: `backend-django/feed/views.py:37-70,132-151`
- Test: `backend-django/feed/tests/test_feed_tie.py` (create)

- [ ] **Step 1: Add a dedup key to each entry builder**

In each of `_rating_entry`, `_review_entry`, `_finished_entry`, add a `"key"` field:
```python
def _rating_entry(r, request):
    return {"type": "rating", "key": ("rating", r.pk), "timestamp": r.updated_at, ...}
def _review_entry(r, request):
    return {"type": "review", "key": ("review", r.pk), "timestamp": r.updated_at, ...}
def _finished_entry(e, request):
    return {"type": "finished", "key": ("finished", e.pk), "timestamp": e.finished_at, ...}
```
(`FeedItemSerializer` ignores the extra `key`; do not declare it on the serializer.)

- [ ] **Step 2: After tie-swallow, pull the complete boundary group from the DB**

Replace the tie-swallow block (lines ~144-151) with:
```python
        i = PAGE_SIZE
        if page:
            boundary = page[-1]["timestamp"]
            while i < len(items) and items[i]["timestamp"] == boundary:
                page.append(items[i])
                i += 1
            # The per-source fetch window can truncate a tie group larger than
            # fetch_size within one source; pull the COMPLETE boundary group so
            # no same-timestamp item is silently skipped by the strict `<` cursor.
            present = {it["key"] for it in page}
            extra = (
                [_rating_entry(r, request) for r in Rating.objects.filter(
                    user_id__in=following_ids, updated_at=boundary).select_related("user", "book")]
                + [_review_entry(r, request) for r in Review.objects.filter(
                    user_id__in=following_ids, updated_at=boundary).select_related("user", "book")]
                + [_finished_entry(e, request) for e in ShelfEntry.objects.filter(
                    user_id__in=following_ids, status=ShelfEntry.Status.READ,
                    finished_at=boundary).select_related("user", "book")]
            )
            for entry in extra:
                if entry["key"] not in present:
                    page.append(entry)
                    present.add(entry["key"])
        has_more = i < len(items)
        next_before = page[-1]["timestamp"].isoformat() if has_more else None
```

- [ ] **Step 3: Write the failing test**

```python
# backend-django/feed/tests/test_feed_tie.py
from django.utils.timezone import now
from rest_framework.test import APITestCase

from books.models import Book
from ratings.models import Rating
from users.models import User, UserFollow


class FeedTieGroupTests(APITestCase):
    def test_large_same_timestamp_group_not_dropped(self):
        me = User.objects.create_user(email="me@e.test", handle="me", password="password123")
        author = User.objects.create_user(
            email="a@e.test", handle="auth", password="password123", profile_public=True
        )
        UserFollow.objects.create(follower=me, following=author)
        ts = now()
        for n in range(22):  # > fetch_size (PAGE_SIZE + 1 = 21)
            b = Book.objects.create(title=f"B{n}", slug=f"b{n}")
            Rating.objects.create(user=author, book=b, rating=4)
        Rating.objects.filter(user=author).update(updated_at=ts)

        self.client.force_authenticate(me)
        res = self.client.get("/api/feed/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data["results"]), 22)
        self.assertIsNone(res.data["next_before"])
```

- [ ] **Step 4: Run test (FAIL before Steps 1-2, PASS after)**

Run: `DJANGO_ENV=dev uv run python -m pytest feed/tests/test_feed_tie.py -v`
Expected: PASS (without the fix it returns ~21, not 22).

- [ ] **Step 5: Commit**

```bash
git add backend-django/feed/views.py backend-django/feed/tests/test_feed_tie.py
git commit -m "fix: feed keeps full same-timestamp tie group"
```

### Task 12: Avatar format validated by Pillow, not client MIME (D3, info)

**Files:**
- Modify: `backend-django/users/serializers.py:191-206`
- Test: `backend-django/users/tests/test_avatar_validation.py` (create)

- [ ] **Step 1: Validate by `img.format`**

```python
    def validate_avatar(self, file):
        if file.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("Avatar must be under 2 MB.")
        from PIL import Image

        allowed_formats = {"JPEG", "PNG", "WEBP"}
        img = Image.open(file)
        detected = img.format  # Pillow-detected, not the spoofable client MIME
        img.verify()
        if detected not in allowed_formats:
            raise serializers.ValidationError("Only JPEG, PNG and WebP are allowed.")
        file.seek(0)
        img = Image.open(file)
        if img.width > 1024 or img.height > 1024:
            raise serializers.ValidationError("Dimensions must not exceed 1024×1024 px.")
        file.seek(0)
        return file
```

- [ ] **Step 2: Write the test**

```python
# backend-django/users/tests/test_avatar_validation.py
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from PIL import Image

from users.serializers import AvatarUploadSerializer


def _img(fmt, content_type, size=(64, 64)):
    buf = io.BytesIO()
    Image.new("RGB", size).save(buf, format=fmt)
    buf.seek(0)
    ext = {"PNG": "png", "GIF": "gif"}[fmt]
    return SimpleUploadedFile(f"a.{ext}", buf.read(), content_type=content_type)


class AvatarValidationTests(SimpleTestCase):
    def test_png_accepted(self):
        s = AvatarUploadSerializer(data={"avatar": _img("PNG", "image/png")})
        self.assertTrue(s.is_valid(), s.errors)

    def test_gif_with_spoofed_jpeg_mime_rejected(self):
        s = AvatarUploadSerializer(data={"avatar": _img("GIF", "image/jpeg")})
        self.assertFalse(s.is_valid())
        self.assertIn("avatar", s.errors)
```

- [ ] **Step 3: Run (FAIL before Step 1, PASS after) + commit**

Run: `DJANGO_ENV=dev uv run python -m pytest users/tests/test_avatar_validation.py -v` → PASS.
```bash
git add backend-django/users/serializers.py backend-django/users/tests/test_avatar_validation.py
git commit -m "fix: validate avatar format via Pillow"
```

### Task 13: Dedup character relations by pk (D4, info)

**Files:**
- Modify: `backend-django/characters/services.py:57-65`
- Test: `backend-django/characters/tests/test_store_characters.py` (create)

- [ ] **Step 1: Build the dedup key from pks, after the guard**

```python
        relation_type = raw_type if raw_type in valid_types else RelationType.OTHER
        if not (source and target and source != target):
            continue
        key = (source.pk, target.pk, relation_type)
        if key in seen:
            continue
        seen.add(key)
        CharacterRelation.objects.create(
            book=book,
            from_character=source,
            to_character=target,
            relation_type=relation_type,
        )
```

- [ ] **Step 2: Write the test**

```python
# backend-django/characters/tests/test_store_characters.py
from django.test import TestCase

from books.models import Book
from characters.models import Character, CharacterRelation
from characters.services import store_characters


class StoreCharactersTests(TestCase):
    def test_duplicate_relation_deduped_and_missing_endpoint_skipped(self):
        book = Book.objects.create(title="T", slug="t")
        data = {
            "characters": [{"name": "Alice"}, {"name": "Bob"}],
            "relations": [
                {"from": "Alice", "to": "Bob", "type": "friend"},
                {"from": "Alice", "to": "Bob", "type": "friend"},  # dup
                {"from": "Alice", "to": "Ghost", "type": "friend"},  # missing endpoint
            ],
        }
        store_characters(book, data)
        self.assertEqual(Character.objects.filter(book=book).count(), 2)
        self.assertEqual(CharacterRelation.objects.filter(book=book).count(), 1)
```

- [ ] **Step 3: Run (FAIL before Step 1 if a regression slips, PASS after) + commit**

Run: `DJANGO_ENV=dev uv run python -m pytest characters/tests/test_store_characters.py -v` → PASS.
```bash
git add backend-django/characters/services.py backend-django/characters/tests/test_store_characters.py
git commit -m "fix: dedup character relations by pk"
```

### Task 14: Comment the intentional email-change session policy (email finding, info)

**Files:**
- Modify: `backend-django/users/views.py` (EmailChangeView, ~line 188-218)

- [ ] **Step 1: Add a clarifying comment**

Just before `user.email = new_email`:
```python
        # Intentional: unlike PasswordChangeView, an email change does NOT
        # blacklist/reissue JWTs. simplejwt tokens are keyed on user id, not
        # email, so existing sessions stay valid; a notice goes to the old
        # address. Keep this asymmetry deliberate.
```

- [ ] **Step 2: Verify + commit**

Run: `cd backend-django && uv run ruff check . && DJANGO_ENV=dev uv run python manage.py check`
```bash
git add backend-django/users/views.py
git commit -m "docs: note email change keeps sessions valid"
```

---

## Group E — Tests + CI

### Task 6: Harden CI test job (E1 + E4, medium + info)

**Files:**
- Modify: `.github/workflows/ci.yml:47-52`

- [ ] **Step 1: Add `check` + migration-drift, drop the duplicate OpenAPI step**

Replace the two steps under the `test` job with:
```yaml
      - name: Django system check
        working-directory: backend-django
        run: DJANGO_ENV=dev uv run python manage.py check
      - name: Check for missing migrations
        working-directory: backend-django
        run: DJANGO_ENV=dev uv run python manage.py makemigrations --check --dry-run
      - name: Run Django tests
        working-directory: backend-django
        run: uv run python -m pytest
```
(The standalone `manage.py test config.tests.test_openapi_schema` step is removed — `pytest` already collects that TestCase via `testpaths=["."]`.)

- [ ] **Step 2: Validate the workflow + commit**

Run: `python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci.yml')); print('OK')"`
Expected: `OK`. Confirm locally that `makemigrations --check --dry-run` exits 0 (no pending migrations).
```bash
git add .github/workflows/ci.yml
git commit -m "ci: add check + migration drift, dedup openapi"
```

### Task 7: Throttle regression tests (E2, medium)

**Files:**
- Test: `backend-django/users/tests/test_throttling.py` (create)
- Test: `backend-django/characters/tests/test_throttling.py` (create)

> Throttling is disabled globally under test (dev.py:22-23). Re-enable `ScopedRateThrottle` with a tiny rate via `override_settings`, clearing the LocMem cache around each test to avoid counter bleed.

- [ ] **Step 1: Register-throttle test**

```python
# backend-django/users/tests/test_throttling.py
from django.core.cache import cache
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from config.settings.base import REST_FRAMEWORK as _RF

_THROTTLED = {
    **_RF,
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.ScopedRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {**_RF["DEFAULT_THROTTLE_RATES"], "auth_register": "2/min"},
}


@override_settings(REST_FRAMEWORK=_THROTTLED)
class RegisterThrottleTests(APITestCase):
    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def _body(self, n):
        return {
            "email": f"u{n}@e.test",
            "handle": f"u{n}",
            "password": "password123",
            "display_name": "U",
        }

    def test_register_429_after_limit(self):
        self.assertEqual(self.client.post("/api/auth/register/", self._body(1), format="json").status_code, status.HTTP_201_CREATED)
        self.client.post("/api/auth/register/", self._body(2), format="json")
        third = self.client.post("/api/auth/register/", self._body(3), format="json")
        self.assertEqual(third.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
```

- [ ] **Step 2: character_generate-throttle test**

```python
# backend-django/characters/tests/test_throttling.py
from django.core.cache import cache
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book
from config.settings.base import REST_FRAMEWORK as _RF
from users.models import User

_THROTTLED = {
    **_RF,
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.ScopedRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {**_RF["DEFAULT_THROTTLE_RATES"], "character_generate": "1/min"},
}


@override_settings(REST_FRAMEWORK=_THROTTLED)
class CharacterGenerateThrottleTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(email="u@e.test", handle="u", password="password123")
        self.book = Book.objects.create(title="T", slug="t")

    def tearDown(self):
        cache.clear()

    def test_generate_429_after_limit(self):
        self.client.force_authenticate(self.user)
        url = f"/api/books/{self.book.slug}/characters/generate/"
        self.assertEqual(self.client.post(url).status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(self.client.post(url).status_code, status.HTTP_429_TOO_MANY_REQUESTS)
```

- [ ] **Step 3: Run both, expect PASS + commit**

Run: `DJANGO_ENV=dev uv run python -m pytest users/tests/test_throttling.py characters/tests/test_throttling.py -v`
Expected: PASS. (If `force_authenticate` bypasses scope counting, the generate test still trips because `ScopedRateThrottle` keys on the authenticated user.)
```bash
git add backend-django/users/tests/test_throttling.py backend-django/characters/tests/test_throttling.py
git commit -m "test: cover register + generate throttles"
```

### Task 8: E2E for character feature (E3, medium)

**Files:**
- Create: `backend-django/characters/management/__init__.py`, `backend-django/characters/management/commands/__init__.py`
- Create: `backend-django/characters/management/commands/seed_characters.py`
- Create: `svelte-frontend/e2e/characters.spec.ts`
- Modify: `.github/workflows/ci.yml` (e2e job seed step)

> There is no API to create characters (only the Celery/LLM path), so add a dev/test-only management command to seed a deterministic analysis + characters + relation, invoke it in the e2e CI setup, and assert the pages render.

- [ ] **Step 1: Seed management command**

```python
# backend-django/characters/management/commands/seed_characters.py
from django.core.management.base import BaseCommand, CommandError

from books.models import Book
from characters.models import Character, CharacterAnalysis, CharacterRelation, unique_character_slug
from characters.relations import RelationType


class Command(BaseCommand):
    help = "Seed a deterministic DONE character analysis for E2E (no LLM)."

    def add_arguments(self, parser):
        parser.add_argument("slug")

    def handle(self, *args, **opts):
        try:
            book = Book.objects.get(slug=opts["slug"])
        except Book.DoesNotExist as exc:
            raise CommandError(f"No book with slug {opts['slug']!r}") from exc

        CharacterRelation.objects.filter(book=book).delete()
        Character.objects.filter(book=book).delete()
        CharacterAnalysis.objects.update_or_create(
            book=book, defaults={"status": CharacterAnalysis.Status.DONE, "error_message": ""}
        )
        frodo = Character.objects.create(
            book=book, name="Frodo", slug=unique_character_slug(book, "Frodo"),
            role="Ring-bearer", description="A hobbit of the Shire.", order=0,
        )
        sam = Character.objects.create(
            book=book, name="Sam", slug=unique_character_slug(book, "Sam"),
            role="Companion", description="Frodo's loyal friend.", order=1,
        )
        CharacterRelation.objects.create(
            book=book, from_character=frodo, to_character=sam, relation_type=RelationType.FRIEND,
        )
        self.stdout.write(self.style.SUCCESS(f"Seeded characters for {book.slug}"))
```

> Confirm `RelationType.FRIEND` exists in `characters/relations.py`; if the member name differs, use any valid `RelationType` value.

- [ ] **Step 2: Add a seed step to the e2e CI job**

In `.github/workflows/ci.yml`, in the e2e job's "Migrate and create e2e admin" step, after the seed books are created by global-setup the slug isn't known at migrate time — instead add a step AFTER "Start Django backend" that seeds against the known title's slug. Simpler: extend the admin step to also seed by the deterministic Fellowship slug once books exist. Since books are seeded by Playwright global-setup (runs inside `npm run test:e2e`), add the character seeding into `global-setup.ts` via an HTTP-free shell is not possible. Instead, run the command in CI right before tests using the slug file:

```yaml
      - name: Seed characters for E2E
        working-directory: backend-django
        run: |
          uv run python manage.py shell -c "from books.models import Book; b=Book.objects.filter(title='The Fellowship of the Ring').first(); print(b.slug if b else '')" > /tmp/slug.txt || true
```
Then guard the spec to skip if unseeded (Step 3). **Preferred:** call the command from the Playwright global-setup after seeding via a tiny `child_process` exec of `manage.py seed_characters <slug>` when running locally, and in CI add an explicit step after global-setup. Implementer: place a `Seed characters` CI step after "Install Playwright browser" that resolves the slug from the books API and runs `manage.py seed_characters <slug>`.

- [ ] **Step 3: Playwright spec**

```ts
// svelte-frontend/e2e/characters.spec.ts
import { test, expect } from './fixtures';

test.describe('Character analysis', () => {
	test('renders seeded characters and detail', async ({ page }) => {
		// Fellowship is seeded by global-setup; characters seeded via manage.py seed_characters.
		await page.goto('/discover');
		await page.getByText('The Fellowship of the Ring').first().click();
		await expect(page).toHaveURL(/\/books\//);
		// Characters section shows the seeded cards
		await expect(page.getByText('Frodo')).toBeVisible();
		await expect(page.getByText('Sam')).toBeVisible();
		await page.getByText('Frodo').first().click();
		await expect(page).toHaveURL(/\/characters\//);
		await expect(page.getByText('Ring-bearer')).toBeVisible();
	});
});
```

> Adjust selectors to the actual character card / detail markup in `src/routes/books/[slug]/characters/`. If seeding can't be guaranteed in a given environment, gate with `test.skip` on absence of the cards.

- [ ] **Step 4: Run + commit**

Run (dev stack + `manage.py seed_characters <fellowship-slug>`): `cd svelte-frontend && npm run test:e2e -- characters.spec.ts` → PASS.
```bash
git add backend-django/characters/management svelte-frontend/e2e/characters.spec.ts .github/workflows/ci.yml
git commit -m "test: e2e for character analysis feature"
```

### Task 18: Remove dead vitest script (E5, low)

**Files:**
- Modify: `svelte-frontend/package.json:13,35,40,49`

- [ ] **Step 1: Delete the `test` script and unused devDeps**

Remove line 13 (`"test": "vitest run",`) and the devDependencies `@vitest/ui`, `jsdom`, `vitest`. (`vite.config.ts` has no `test` block, confirmed — nothing else references them.)

- [ ] **Step 2: Refresh lockfile + verify**

Run: `cd svelte-frontend && npm install && npm run check && npm run lint && npm run build`
Expected: all succeed; `package-lock.json` updated.

- [ ] **Step 3: Commit**

```bash
git add svelte-frontend/package.json svelte-frontend/package-lock.json
git commit -m "chore: remove dead vitest script and deps"
```

### Task 19: Make discover E2E counts robust (E6, low)

**Files:**
- Modify: `svelte-frontend/e2e/discover.spec.ts:21-28,51-61`

- [ ] **Step 1: Replace exact global counts with presence of seeded items**

`renders 5 seeded book cards` → assert each seeded title is visible and `toHaveCount` ≥ is avoided; instead:
```ts
	test('renders the seeded book cards', async ({ page }) => {
		for (const title of ['The Fellowship of the Ring', 'Dune', '1984', 'The Hobbit', 'The Two Towers']) {
			await expect(page.locator('.grid h3', { hasText: title })).toBeVisible();
		}
	});
```
`genre filter shows only matching book` → assert the three Fantasy titles are visible and a non-Fantasy one (`Dune`) is not, instead of `toHaveCount(3)`:
```ts
		await listbox.getByText('fantasy').click();
		for (const t of ['The Fellowship of the Ring', 'The Hobbit', 'The Two Towers']) {
			await expect(page.locator('.grid h3', { hasText: t })).toBeVisible();
		}
		await expect(page.locator('.grid h3', { hasText: 'Dune' })).toHaveCount(0);
```
(Leave the `search filters by title` toHaveCount(1) tests — a unique title match is robust.)

- [ ] **Step 2: Run + commit**

Run (dev stack): `cd svelte-frontend && npm run test:e2e -- discover.spec.ts` → PASS.
```bash
git add svelte-frontend/e2e/discover.spec.ts
git commit -m "test: make discover e2e seed-pollution proof"
```

---

## Group F — Docs

### Task 9: Fix ADR-002 reverse-proxy directive (F1, medium)

**Files:**
- Modify: `docs/decisions/ADR-002-client-api-same-origin.md:21`

- [ ] **Step 1: Correct `handle_path` → `handle`**

Change the prose so it matches the Caddyfile (which uses `handle /api/*` to preserve the prefix):
```
... this is Caddy (`handle /api/* → reverse_proxy django:8000`, preserving the
/api prefix; `handle_path` would strip it and 404) ...
```

- [ ] **Step 2: Commit**

```bash
git add docs/decisions/ADR-002-client-api-same-origin.md
git commit -m "docs: fix ADR-002 caddy directive to handle"
```

### Task 20: Fix ARCHITECTURE model diagram (F2, low)

**Files:**
- Modify: `docs/ARCHITECTURE.md` (Model relations block, the Book / Character lines)

- [ ] **Step 1: Redraw so Book owns Character + CharacterRelation**

Replace the `CharacterAnalysis (OneToOne) ── Character ── CharacterRelation` line with:
```
 ├── CharacterAnalysis (OneToOne) — generation status only
 ├── Character (FK Book) ── CharacterRelation (from/to Character, relation_type)
```
(Each is a direct child of `Book`; `CharacterAnalysis` is a sibling status record, not the parent of `Character`.)

- [ ] **Step 2: Commit**

```bash
git add docs/ARCHITECTURE.md
git commit -m "docs: fix character model ownership diagram"
```

---

## Group A (continued) — lower-priority hardening

### Task 21: Non-root containers (A3, low)

**Files:**
- Modify: `backend-django/Dockerfile`
- Modify: `svelte-frontend/Dockerfile.prod`

- [ ] **Step 1: Django image — add an app user, own writable paths**

After `RUN uv run python manage.py collectstatic --noinput` and before `EXPOSE 8000`:
```dockerfile
RUN useradd --create-home --uid 1000 app \
    && mkdir -p /app/media \
    && chown -R app:app /app/media /app/staticfiles
USER app
```

- [ ] **Step 2: Svelte image — run as the built-in node user**

Before `CMD ["node", "build/index.js"]` in the runner stage:
```dockerfile
USER node
```

- [ ] **Step 3: Build both images locally**

Run: `docker build -t ss-django-test backend-django && docker build -f svelte-frontend/Dockerfile.prod -t ss-svelte-test svelte-frontend`
Expected: both build; containers would run as non-root (`USER` set). The `media` named volume inherits `app` ownership on first creation.

- [ ] **Step 4: Commit**

```bash
git add backend-django/Dockerfile svelte-frontend/Dockerfile.prod
git commit -m "fix: run prod containers as non-root"
```

### Task 22 (OPTIONAL): Serve /media via Caddy (A4, low)

> Optional / can be deferred as follow-up (spec). Only `/media` (user uploads, on the shared `media` volume) is moved; `/static` stays Django-served (not a shared volume). Skip this task if it complicates the volume wiring — leave a note in the PR.

**Files:**
- Modify: `infra/compose/docker-compose.prod.yml` (caddy volumes)
- Modify: `infra/caddy/Caddyfile:20-23`

- [ ] **Step 1: Mount the media volume into Caddy (read-only)**

In the `caddy` service `volumes:`:
```yaml
      - media:/srv/media:ro
```

- [ ] **Step 2: Serve /media with file_server**

Replace the Caddyfile `/media` handle:
```
	handle_path /media/* {
		root * /srv/media
		file_server
	}
```

- [ ] **Step 3: Verify config + commit**

Run: `docker compose -f infra/compose/docker-compose.prod.yml config >/dev/null && echo OK`
```bash
git add infra/compose/docker-compose.prod.yml infra/caddy/Caddyfile
git commit -m "perf: serve media via caddy file_server"
```

---

## Final steps (after all tasks)

- [ ] **Full verify**

Run: `make verify` (backend lint + tests) and `cd svelte-frontend && npm run check && npm run lint && npm run build`. With dev stack: `npm run test:e2e`.
Expected: all green.

- [ ] **Remove spec + plan (repo convention, commit #2)**

```bash
git rm docs/superpowers/specs/2026-06-17-audit-fixes-design.md docs/superpowers/plans/2026-06-17-audit-fixes.md
git commit -m "chore: drop audit-fix spec and plan"
```

- [ ] **Hand off for code review** (`/requesting-code-review`), then PR (`/finishing-a-development-branch`). Squash on merge only if the user asks.

---

## Self-review — spec coverage

| Spec item | Task |
|-----------|------|
| A1 Caddy env_file | Task 1 |
| A2 ALLOWED_HOSTS | Task 2 |
| A3 non-root | Task 21 |
| A4 media via Caddy | Task 22 (optional) |
| B1+B2 SSR refresh | Task 4 |
| B3 password cookies | Task 5 |
| C1 navbar search | Task 3 |
| C2 export POST | Task 15 |
| C3 aria-labels | Task 16 |
| C4 listbox roles | Task 17 |
| D1 register throttle | Task 10 |
| D2 feed tie group | Task 11 |
| D3 avatar format | Task 12 |
| D4 relation dedup | Task 13 |
| D5 email comment (was won't-fix→comment) | Task 14 |
| E1 CI check/migrations | Task 6 |
| E2 throttle tests | Task 7 |
| E3 character E2E | Task 8 |
| E4 dedup OpenAPI step | Task 6 |
| E5 vitest dead script | Task 18 |
| E6 discover counts | Task 19 |
| F1 ADR-002 | Task 9 |
| F2 ARCHITECTURE diagram | Task 20 |

Won't-fix (no task, documented in spec): ratings signal lock, review like COUNT, infra/.env, ci.yml deploy step, playwright Vite-vs-prod.
