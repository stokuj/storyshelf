# M9 Reading Stats Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Per-user private reading statistics — an aggregation API (`GET /api/users/me/stats/`) plus a `/stats` frontend page with hand-rolled bar charts.

**Architecture:** A pure aggregation function (`users/stats.py::build_user_stats`) reads `ShelfEntry`, `Rating`, `Book` and returns a plain dict; a thin `MyStatsView` (DRF `APIView`, auth-only) serializes it via `UserStatsSerializer` (also the OpenAPI contract). A small change to `ShelfEntrySerializer` auto-sets `finish_date` the first time an entry becomes `READ`, so date-based stats have data. Frontend adds `/stats` (SSR load) and a reusable `BarChart.svelte` (CSS bars, no chart library).

**Tech Stack:** Django 6 + DRF + drf-spectacular (backend), SvelteKit 2 + Svelte 5 + Tailwind v4 (frontend). Tests: Django `APITestCase`; `npm run check`/`lint`.

---

## File Structure

| File | Create/Modify | Responsibility |
|------|---------------|----------------|
| `backend-django/shelf/serializers.py` | Modify | Auto-set `finish_date` on transition to `READ` |
| `backend-django/shelf/tests/test_api.py` | Modify | Tests for the auto-set behaviour |
| `backend-django/users/stats.py` | Create | Pure `build_user_stats(user) -> dict` aggregation |
| `backend-django/users/tests/test_stats.py` | Create | Unit + endpoint tests for stats |
| `backend-django/users/serializers.py` | Modify | `UserStatsSerializer` (+ nested) for response/contract |
| `backend-django/users/views.py` | Modify | `MyStatsView` |
| `backend-django/users/urls/users.py` | Modify | Route `me/stats/` |
| `docs/api/openapi.yml` | Modify (generated) | OpenAPI snapshot |
| `svelte-frontend/src/lib/api/stats.ts` | Create | `getMyStats` + `UserStats` type |
| `svelte-frontend/src/lib/components/stats/BarChart.svelte` | Create | Reusable CSS bar chart |
| `svelte-frontend/src/routes/stats/+page.server.ts` | Create | SSR load of stats |
| `svelte-frontend/src/routes/stats/+page.svelte` | Create | Stats page layout |
| `svelte-frontend/src/lib/components/shell/AppShell.svelte` | Modify | Nav link "Stats" (auth-guarded) |

**Test command (backend):** all backend test runs use `DJANGO_ENV=dev` from `backend-django/`:
```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test <dotted.path> -v 2
```

---

## Task 1: Auto-set `finish_date` on transition to READ

**Files:**
- Modify: `backend-django/shelf/serializers.py` (inside `ShelfEntrySerializer.validate`)
- Test: `backend-django/shelf/tests/test_api.py` (append a new test class)

- [ ] **Step 1: Write the failing tests**

Append to `backend-django/shelf/tests/test_api.py` (the file already imports `date`, `status`, `ShelfEntry`, `User`, `Book`, etc. and defines `URL = "/api/shelf/entries/"`):

```python
class FinishDateAutoSetTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="fd@test.com", handle="finn", password="password123"
        )
        cls.book = Book.objects.create(title="Dune", slug="dune", page_count=412)
        cls.today = date.today()

    def _detail(self, pk):
        return f"{URL}{pk}/"

    def test_patch_to_read_sets_finish_date(self):
        self.client.force_authenticate(self.user)
        entry = ShelfEntry.objects.create(user=self.user, book=self.book)
        resp = self.client.patch(
            self._detail(entry.pk), {"status": "READ"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["finish_date"], self.today.isoformat())

    def test_create_as_read_sets_finish_date(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            URL, {"book_slug": "dune", "status": "READ"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["finish_date"], self.today.isoformat())

    def test_existing_finish_date_not_overwritten(self):
        self.client.force_authenticate(self.user)
        entry = ShelfEntry.objects.create(
            user=self.user, book=self.book, status="READ",
            finish_date=date(2020, 1, 1),
        )
        resp = self.client.patch(
            self._detail(entry.pk), {"current_page": 10}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["finish_date"], "2020-01-01")

    def test_explicit_finish_date_respected(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            URL,
            {"book_slug": "dune", "status": "READ", "finish_date": "2019-05-05"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["finish_date"], "2019-05-05")

    def test_non_read_status_does_not_set_finish_date(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            URL, {"book_slug": "dune", "status": "READING"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(resp.data["finish_date"])
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test shelf.tests.test_api.FinishDateAutoSetTest -v 2
```
Expected: FAIL — `test_patch_to_read_sets_finish_date`, `test_create_as_read_sets_finish_date` fail because `finish_date` is `None` (auto-set not implemented yet). The other three should already pass.

- [ ] **Step 3: Add the `date` import**

At the top of `backend-django/shelf/serializers.py`, add after the existing imports block (the file currently starts with `from django.core.exceptions import ...`):

```python
from datetime import date
```

- [ ] **Step 4: Implement the auto-set in `validate`**

In `backend-django/shelf/serializers.py`, inside `ShelfEntrySerializer.validate`, insert the following block **after** the "Book is immutable after creation" check and **before** the `# Reuse model.clean()` block (so `entry.clean()` validates the freshly set date):

```python
        # Auto-set finish_date the first time an entry becomes READ, so reading
        # stats (books/year, time-on-shelf) have a date to work with. Never
        # overwrite an existing or explicitly-provided finish_date.
        result_status = attrs.get("status", getattr(self.instance, "status", None))
        if (
            result_status == ShelfEntry.Status.READ
            and "finish_date" not in attrs
            and getattr(self.instance, "finish_date", None) is None
        ):
            attrs["finish_date"] = date.today()
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test shelf.tests.test_api.FinishDateAutoSetTest -v 2
```
Expected: PASS (5 tests).

- [ ] **Step 6: Run the full shelf suite (no regressions)**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test shelf -v 1
```
Expected: PASS (all existing shelf tests still green).

- [ ] **Step 7: Commit**

```bash
git add backend-django/shelf/serializers.py backend-django/shelf/tests/test_api.py
git commit -m "feat: auto-set finish_date on READ"
```

---

## Task 2: `build_user_stats` aggregation function

**Files:**
- Create: `backend-django/users/stats.py`
- Test: `backend-django/users/tests/test_stats.py`

- [ ] **Step 1: Write the failing unit tests**

Create `backend-django/users/tests/test_stats.py`:

```python
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

from books.models import Book
from ratings.models import Rating
from shelf.models import ShelfEntry
from users.stats import build_user_stats

User = get_user_model()


class BuildUserStatsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="s@test.com", handle="stan", password="password123"
        )
        cls.b1 = Book.objects.create(title="B1", slug="b1", page_count=100)
        cls.b2 = Book.objects.create(title="B2", slug="b2", page_count=200)
        cls.b3 = Book.objects.create(title="B3", slug="b3", page_count=None)

        # Two READ (with finish dates), one READING, one WANT_TO_READ.
        ShelfEntry.objects.create(
            user=cls.user, book=cls.b1, status="READ",
            finish_date=date(2025, 3, 1),
        )
        ShelfEntry.objects.create(
            user=cls.user, book=cls.b2, status="READ",
            finish_date=date(2026, 1, 10),
        )
        ShelfEntry.objects.create(user=cls.user, book=cls.b3, status="READING")

        # Ratings: 5, 3.
        Rating.objects.create(user=cls.user, book=cls.b1, rating=5)
        Rating.objects.create(user=cls.user, book=cls.b2, rating=3)

    def test_status_counts(self):
        stats = build_user_stats(self.user)
        self.assertEqual(
            stats["status_counts"],
            {"want_to_read": 0, "reading": 1, "read": 2},
        )

    def test_totals(self):
        stats = build_user_stats(self.user)
        self.assertEqual(stats["totals"]["total_books"], 3)
        # pages_read = sum of READ books with page_count (100 + 200).
        self.assertEqual(stats["totals"]["pages_read"], 300)
        self.assertEqual(stats["totals"]["avg_rating_given"], 4.0)

    def test_books_per_year(self):
        stats = build_user_stats(self.user)
        self.assertEqual(
            stats["books_per_year"],
            [{"year": 2025, "count": 1}, {"year": 2026, "count": 1}],
        )

    def test_rating_distribution_zero_filled(self):
        stats = build_user_stats(self.user)
        self.assertEqual(
            stats["rating_distribution"],
            [
                {"rating": 1, "count": 0},
                {"rating": 2, "count": 0},
                {"rating": 3, "count": 1},
                {"rating": 4, "count": 0},
                {"rating": 5, "count": 1},
            ],
        )

    def test_time_on_shelf_days(self):
        # Both READ entries were created today (auto_now_add), finished in the
        # past relative to nothing — created_at is "now", finish_date is fixed.
        # So delta = finish_date - today (can be negative); assert it is a float.
        stats = build_user_stats(self.user)
        self.assertIsInstance(stats["time_on_shelf_days"], float)

    def test_empty_user(self):
        empty = User.objects.create_user(
            email="e@test.com", handle="empty", password="password123"
        )
        stats = build_user_stats(empty)
        self.assertEqual(
            stats["status_counts"], {"want_to_read": 0, "reading": 0, "read": 0}
        )
        self.assertEqual(stats["totals"]["total_books"], 0)
        self.assertEqual(stats["totals"]["pages_read"], 0)
        self.assertIsNone(stats["totals"]["avg_rating_given"])
        self.assertEqual(stats["books_per_year"], [])
        self.assertEqual(
            stats["rating_distribution"],
            [{"rating": r, "count": 0} for r in range(1, 6)],
        )
        self.assertIsNone(stats["time_on_shelf_days"])

    def test_only_own_data(self):
        other = User.objects.create_user(
            email="o@test.com", handle="otto", password="password123"
        )
        ShelfEntry.objects.create(user=other, book=self.b1, status="READ")
        Rating.objects.create(user=other, book=self.b1, rating=1)
        stats = build_user_stats(self.user)
        # Unchanged by other user's data.
        self.assertEqual(stats["status_counts"]["read"], 2)
        self.assertEqual(stats["totals"]["avg_rating_given"], 4.0)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test users.tests.test_stats.BuildUserStatsTest -v 2
```
Expected: FAIL — `ModuleNotFoundError: No module named 'users.stats'`.

- [ ] **Step 3: Implement `build_user_stats`**

Create `backend-django/users/stats.py`:

```python
from django.db.models import Avg, Count, Sum
from django.db.models.functions import ExtractYear

from ratings.models import Rating
from shelf.models import ShelfEntry


def build_user_stats(user) -> dict:
    """Aggregate one user's reading statistics into a plain dict.

    Pure read-only aggregation over ShelfEntry / Rating / Book. Shape matches
    UserStatsSerializer. All values are own-user only.
    """
    entries = ShelfEntry.objects.filter(user=user)

    by_status = {
        row["status"]: row["n"]
        for row in entries.values("status").annotate(n=Count("id"))
    }
    status_counts = {
        "want_to_read": by_status.get(ShelfEntry.Status.WANT_TO_READ, 0),
        "reading": by_status.get(ShelfEntry.Status.READING, 0),
        "read": by_status.get(ShelfEntry.Status.READ, 0),
    }

    read_entries = entries.filter(status=ShelfEntry.Status.READ)
    pages_read = read_entries.aggregate(s=Sum("book__page_count"))["s"] or 0

    avg = Rating.objects.filter(user=user).aggregate(a=Avg("rating"))["a"]
    avg_rating_given = round(avg, 1) if avg is not None else None

    totals = {
        "total_books": entries.count(),
        "pages_read": pages_read,
        "avg_rating_given": avg_rating_given,
    }

    per_year = (
        read_entries.filter(finish_date__isnull=False)
        .annotate(year=ExtractYear("finish_date"))
        .values("year")
        .annotate(count=Count("id"))
        .order_by("year")
    )
    books_per_year = [{"year": row["year"], "count": row["count"]} for row in per_year]

    rating_map = {
        row["rating"]: row["n"]
        for row in Rating.objects.filter(user=user)
        .values("rating")
        .annotate(n=Count("id"))
    }
    rating_distribution = [
        {"rating": r, "count": rating_map.get(r, 0)} for r in range(1, 6)
    ]

    pairs = read_entries.filter(finish_date__isnull=False).values_list(
        "created_at", "finish_date"
    )
    deltas = [(finish - created.date()).days for created, finish in pairs]
    time_on_shelf_days = round(sum(deltas) / len(deltas), 1) if deltas else None

    return {
        "status_counts": status_counts,
        "totals": totals,
        "books_per_year": books_per_year,
        "rating_distribution": rating_distribution,
        "time_on_shelf_days": time_on_shelf_days,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test users.tests.test_stats.BuildUserStatsTest -v 2
```
Expected: PASS (8 tests).

- [ ] **Step 5: Commit**

```bash
git add backend-django/users/stats.py backend-django/users/tests/test_stats.py
git commit -m "feat: add build_user_stats aggregation"
```

---

## Task 3: `UserStatsSerializer` (response + OpenAPI contract)

**Files:**
- Modify: `backend-django/users/serializers.py` (append at end)

- [ ] **Step 1: Add the serializers**

Append to `backend-django/users/serializers.py` (the file already does `from rest_framework import serializers`):

```python
class _StatusCountsSerializer(serializers.Serializer):
    want_to_read = serializers.IntegerField()
    reading = serializers.IntegerField()
    read = serializers.IntegerField()


class _StatsTotalsSerializer(serializers.Serializer):
    total_books = serializers.IntegerField()
    pages_read = serializers.IntegerField()
    avg_rating_given = serializers.FloatField(allow_null=True)


class _YearCountSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    count = serializers.IntegerField()


class _RatingCountSerializer(serializers.Serializer):
    rating = serializers.IntegerField()
    count = serializers.IntegerField()


class UserStatsSerializer(serializers.Serializer):
    status_counts = _StatusCountsSerializer()
    totals = _StatsTotalsSerializer()
    books_per_year = _YearCountSerializer(many=True)
    rating_distribution = _RatingCountSerializer(many=True)
    time_on_shelf_days = serializers.FloatField(allow_null=True)
```

- [ ] **Step 2: Verify it imports (sanity check)**

```bash
cd backend-django && DJANGO_ENV=dev uv run python -c "from users.serializers import UserStatsSerializer; print('ok')"
```
Expected: prints `ok`.

- [ ] **Step 3: Commit**

```bash
git add backend-django/users/serializers.py
git commit -m "feat: add UserStatsSerializer"
```

---

## Task 4: `MyStatsView` + URL + endpoint tests

**Files:**
- Modify: `backend-django/users/views.py`
- Modify: `backend-django/users/urls/users.py`
- Test: `backend-django/users/tests/test_stats.py` (append endpoint test class)

- [ ] **Step 1: Write the failing endpoint tests**

Append to `backend-django/users/tests/test_stats.py`:

```python
from rest_framework import status as http_status
from rest_framework.test import APITestCase

STATS_URL = "/api/users/me/stats/"


class MyStatsEndpointTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="me@test.com", handle="mona", password="password123"
        )
        book = Book.objects.create(title="X", slug="x", page_count=120)
        ShelfEntry.objects.create(
            user=cls.user, book=book, status="READ", finish_date=date(2025, 6, 1)
        )
        Rating.objects.create(user=cls.user, book=book, rating=4)

    def test_requires_auth(self):
        resp = self.client.get(STATS_URL)
        self.assertEqual(resp.status_code, http_status.HTTP_401_UNAUTHORIZED)

    def test_returns_stats_shape(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(STATS_URL)
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        self.assertEqual(
            set(resp.data.keys()),
            {
                "status_counts",
                "totals",
                "books_per_year",
                "rating_distribution",
                "time_on_shelf_days",
            },
        )
        self.assertEqual(resp.data["status_counts"]["read"], 1)
        self.assertEqual(resp.data["totals"]["pages_read"], 120)
        self.assertEqual(resp.data["books_per_year"], [{"year": 2025, "count": 1}])
        self.assertEqual(len(resp.data["rating_distribution"]), 5)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test users.tests.test_stats.MyStatsEndpointTest -v 2
```
Expected: FAIL — 404 (route not wired) / import error.

- [ ] **Step 3: Add the view**

In `backend-django/users/views.py`:

a) Add `extend_schema` to the drf-spectacular import. There is currently no `drf_spectacular` import in this file, so add a new import line near the top (after the `rest_framework` imports):

```python
from drf_spectacular.utils import extend_schema
```

b) Add `UserStatsSerializer` to the existing `from users.serializers import (...)` block (keep alphabetical-ish ordering, place after `UserSettingsPatchSerializer`):

```python
    UserStatsSerializer,
```

c) Add the import for the aggregation function near the other `users.*` imports:

```python
from users.stats import build_user_stats
```

d) Append the view at the end of the file:

```python
class MyStatsView(views.APIView):
    """Own reading statistics. Authenticated; own data only."""

    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(responses=UserStatsSerializer)
    def get(self, request):
        data = build_user_stats(request.user)
        return Response(UserStatsSerializer(data).data)
```

- [ ] **Step 4: Wire the URL**

In `backend-django/users/urls/users.py`:

a) Add `MyStatsView` to the import block:

```python
from users.views import (
    AvatarUploadView,
    DataExportView,
    EmailChangeView,
    FollowListView,
    MyStatsView,
    PasswordChangeView,
    UserFollowView,
    UserMeView,
    UserSettingsView,
)
```

b) Add the route after `me/export/`:

```python
    path("me/stats/", MyStatsView.as_view()),
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test users.tests.test_stats -v 2
```
Expected: PASS (all stats tests, unit + endpoint).

- [ ] **Step 6: Commit**

```bash
git add backend-django/users/views.py backend-django/users/urls/users.py backend-django/users/tests/test_stats.py
git commit -m "feat: add GET /users/me/stats endpoint"
```

---

## Task 5: Regenerate OpenAPI snapshot + contract test

**Files:**
- Modify: `docs/api/openapi.yml` (generated)

- [ ] **Step 1: Regenerate the snapshot**

```bash
make regenerate-openapi
```
Expected: prints `OpenAPI snapshot updated: .../docs/api/openapi.yml`. The diff should add the `/api/users/me/stats/` path and the `UserStats` schema.

- [ ] **Step 2: Run the contract test**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test config.tests.test_openapi_schema -v 2
```
Expected: PASS (live schema matches the regenerated snapshot).

- [ ] **Step 3: Commit**

```bash
git add docs/api/openapi.yml
git commit -m "docs: regenerate OpenAPI for stats endpoint"
```

---

## Task 6: Frontend API client + type

**Files:**
- Create: `svelte-frontend/src/lib/api/stats.ts`

- [ ] **Step 1: Create the client**

Create `svelte-frontend/src/lib/api/stats.ts`:

```ts
import { apiFetch } from './_client';

export interface UserStats {
	status_counts: { want_to_read: number; reading: number; read: number };
	totals: { total_books: number; pages_read: number; avg_rating_given: number | null };
	books_per_year: { year: number; count: number }[];
	rating_distribution: { rating: number; count: number }[];
	time_on_shelf_days: number | null;
}

export function getMyStats(fetchFn: typeof fetch, isServerSide = false) {
	return apiFetch<UserStats>(fetchFn, '/users/me/stats/', undefined, isServerSide);
}
```

- [ ] **Step 2: Commit**

```bash
git add svelte-frontend/src/lib/api/stats.ts
git commit -m "feat: add stats API client"
```

---

## Task 7: `BarChart.svelte` component

**Files:**
- Create: `svelte-frontend/src/lib/components/stats/BarChart.svelte`

- [ ] **Step 1: Create the component**

Create `svelte-frontend/src/lib/components/stats/BarChart.svelte`:

```svelte
<script lang="ts">
	interface Bar {
		label: string;
		value: number;
	}

	let { bars, ariaLabel = 'Bar chart' }: { bars: Bar[]; ariaLabel?: string } = $props();

	// Normalize bar heights to the tallest bar; floor at 1 to avoid /0.
	const max = $derived(Math.max(1, ...bars.map((b) => b.value)));
</script>

{#if bars.length === 0}
	<p class="text-sm text-muted">No data yet</p>
{:else}
	<div class="space-y-2" role="img" aria-label={ariaLabel}>
		<div class="flex items-end gap-2 h-40">
			{#each bars as bar (bar.label)}
				<div
					class="flex-1 rounded-t bg-accent min-h-[2px] transition-[height]"
					style="height: {(bar.value / max) * 100}%"
					title="{bar.label}: {bar.value}"
				></div>
			{/each}
		</div>
		<div class="flex gap-2">
			{#each bars as bar (bar.label)}
				<div class="flex-1 text-center">
					<div class="text-xs font-medium text-ink">{bar.value}</div>
					<div class="text-xs text-muted">{bar.label}</div>
				</div>
			{/each}
		</div>
	</div>
{/if}
```

- [ ] **Step 2: Commit**

```bash
git add svelte-frontend/src/lib/components/stats/BarChart.svelte
git commit -m "feat: add BarChart component"
```

---

## Task 8: `/stats` route (SSR load + page)

**Files:**
- Create: `svelte-frontend/src/routes/stats/+page.server.ts`
- Create: `svelte-frontend/src/routes/stats/+page.svelte`

- [ ] **Step 1: Create the loader**

Create `svelte-frontend/src/routes/stats/+page.server.ts`:

```ts
import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { getMyStats } from '$lib/api/stats';

export const load: PageServerLoad = async ({ fetch }) => {
	const { data, error: err } = await getMyStats(fetch, true);
	if (err || !data) {
		throw error(err?.status || 500, err?.detail || 'Failed to load stats');
	}
	return { stats: data };
};
```

- [ ] **Step 2: Create the page**

Create `svelte-frontend/src/routes/stats/+page.svelte`:

```svelte
<script lang="ts">
	import { Card } from '$lib/components/ui/card';
	import BarChart from '$lib/components/stats/BarChart.svelte';
	import type { UserStats } from '$lib/api/stats';

	let { data }: { data: { stats: UserStats } } = $props();
	const stats = $derived(data.stats);

	const yearBars = $derived(
		stats.books_per_year.map((y) => ({ label: String(y.year), value: y.count }))
	);
	const ratingBars = $derived(
		stats.rating_distribution.map((r) => ({ label: `${r.rating}★`, value: r.count }))
	);
</script>

<svelte:head>
	<title>Reading Stats — Storyshelf</title>
</svelte:head>

<div class="max-w-[1240px] mx-auto px-6 md:px-10 py-8 space-y-8">
	<h1 class="font-display text-2xl font-semibold text-ink">Reading stats</h1>

	<!-- Status counts -->
	<div class="grid grid-cols-3 gap-4">
		<Card class="p-5 text-center">
			<div class="text-2xl font-semibold text-ink">{stats.status_counts.want_to_read}</div>
			<div class="text-xs text-muted mt-1">Want to read</div>
		</Card>
		<Card class="p-5 text-center">
			<div class="text-2xl font-semibold text-ink">{stats.status_counts.reading}</div>
			<div class="text-xs text-muted mt-1">Reading</div>
		</Card>
		<Card class="p-5 text-center">
			<div class="text-2xl font-semibold text-ink">{stats.status_counts.read}</div>
			<div class="text-xs text-muted mt-1">Read</div>
		</Card>
	</div>

	<!-- Totals -->
	<div class="grid grid-cols-3 gap-4">
		<Card class="p-5 text-center">
			<div class="text-2xl font-semibold text-ink">{stats.totals.pages_read}</div>
			<div class="text-xs text-muted mt-1">Pages read</div>
		</Card>
		<Card class="p-5 text-center">
			<div class="text-2xl font-semibold text-ink">
				{stats.totals.avg_rating_given ?? '—'}
			</div>
			<div class="text-xs text-muted mt-1">Avg rating given</div>
		</Card>
		<Card class="p-5 text-center">
			<div class="text-2xl font-semibold text-ink">
				{stats.time_on_shelf_days ?? '—'}
			</div>
			<div class="text-xs text-muted mt-1">Avg days on shelf</div>
		</Card>
	</div>

	<!-- Books per year -->
	<Card class="p-5">
		<h2 class="font-sans text-base font-semibold text-ink mb-4">Books read per year</h2>
		<BarChart bars={yearBars} ariaLabel="Books read per year" />
	</Card>

	<!-- Rating distribution -->
	<Card class="p-5">
		<h2 class="font-sans text-base font-semibold text-ink mb-4">Your ratings</h2>
		<BarChart bars={ratingBars} ariaLabel="Rating distribution" />
	</Card>
</div>
```

- [ ] **Step 3: Verify it builds / type-checks**

```bash
cd svelte-frontend && npm run check
```
Expected: no errors (0 errors, warnings tolerated as in the rest of the repo).

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/src/routes/stats/+page.server.ts svelte-frontend/src/routes/stats/+page.svelte
git commit -m "feat: add /stats page"
```

---

## Task 9: Nav link in AppShell

**Files:**
- Modify: `svelte-frontend/src/lib/components/shell/AppShell.svelte`

- [ ] **Step 1: Add the link**

In `svelte-frontend/src/lib/components/shell/AppShell.svelte`, inside the `{#if user}` block in the `<nav>`, add a Stats link after the Shelf button:

```svelte
				{#if user}
					<Button variant="ghost" size="sm" href={resolve('/shelf')}>Shelf</Button>
					<Button variant="ghost" size="sm" href={resolve('/stats')}>Stats</Button>
				{/if}
```

- [ ] **Step 2: Verify type-check**

```bash
cd svelte-frontend && npm run check
```
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add svelte-frontend/src/lib/components/shell/AppShell.svelte
git commit -m "feat: add Stats nav link"
```

---

## Task 10: Final verification

- [ ] **Step 1: Backend — full suite**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test -v 1
```
Expected: all green.

- [ ] **Step 2: Backend — lint**

```bash
cd backend-django && uv run ruff check .
```
Expected: no errors.

- [ ] **Step 3: Frontend — check + lint**

```bash
cd svelte-frontend && npm run check && npm run lint
```
Expected: 0 errors.

- [ ] **Step 4: Optional manual smoke (dev stack)**

If the dev stack is up (`make dev-up`): log in, mark a book `READ` on `/shelf`, open `/stats`, confirm the "Read" count and "Books read per year" bar reflect it. (Skip if not running a stack.)

- [ ] **Step 5: Done** — proceed to `/requesting-code-review`.

---

## Self-Review notes

- **Spec coverage:** D1 auto-set finish_date → Task 1. D2 endpoint own-only + 401 → Task 4. D3 manual bars → Task 7. D4 `/stats` route → Task 8. D5 no new app (logic in `users/`) → Tasks 2–4. Rating distribution / books-per-year / time-on-shelf / status counts / totals → Task 2 + tests. OpenAPI contract → Task 5. Nav → Task 9. Empty states → BarChart "No data yet" (Task 7) + `—` fallbacks (Task 8).
- **Types consistent:** `build_user_stats` dict keys ↔ `UserStatsSerializer` fields ↔ `UserStats` TS interface ↔ `/stats` page usage all use the same names (`status_counts`, `totals.pages_read`, `books_per_year[].year/count`, `rating_distribution[].rating/count`, `time_on_shelf_days`).
- **No public stats / no start_date / no chart lib** — explicitly out of scope per spec.
- **Note on E2E:** spec marked E2E optional; omitted from the plan to avoid a flaky finish_date-dependent scenario. Manual smoke (Task 10 Step 4) covers the happy path.
