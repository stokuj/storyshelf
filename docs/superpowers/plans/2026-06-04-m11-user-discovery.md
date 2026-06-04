# M11 — Discover users + cudza półka — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pozwolić znaleźć innych czytelników (`/users`) i podejrzeć ich domyślną półkę na publicznym profilu — domyka M6 Follow.

**Architecture:** Dwa nowe read-only endpointy DRF (lista publicznych profili z paginacją/search/ordering; publiczna domyślna półka bramkowana `profile_public`), oba reużywające istniejących wzorców (`StandardPagination`, `_public_owner_or_404`, `ShelfBookSerializer`, adnotacja `user_rating`). Frontend: nowa trasa `/users` (wzorzec paginacji „load more" jak `/discover`), sekcja „Reading" na `/u/[handle]`, rozszerzony `UserRow`, link „People" w nav.

**Tech Stack:** Django 6 + DRF (`generics.ListAPIView`, `SearchFilter`, `OrderingFilter`), SvelteKit 2 + Svelte 5 runes, Playwright E2E.

**Branch:** `feat/m11-user-discovery`. Spec: `docs/superpowers/specs/2026-06-04-m11-user-discovery-design.md`.

**Testowanie backendu (ważne):** z katalogu `backend-django/`, z DB w kontenerze:
```bash
DJANGO_ENV=dev DATABASE_URL='postgres://postgres:CHANGE_ME@localhost:5432/booksdb' uv run python manage.py test users shelf
```

---

## File Structure

| Plik | Odpowiedzialność | Akcja |
|------|------------------|-------|
| `backend-django/users/serializers.py` | `UserListSerializer` (compact card + followers_count) | Modify |
| `backend-django/users/views.py` | `UserListView` (lista publicznych profili) | Modify |
| `backend-django/users/urls/users.py` | trasa `GET /api/users/` | Modify |
| `backend-django/users/tests/test_user_list.py` | testy listy | Create |
| `backend-django/shelf/serializers.py` | `PublicShelfEntrySerializer` (read-only) | Modify |
| `backend-django/shelf/views.py` | `PublicShelfEntryListView` | Modify |
| `backend-django/config/urls.py` | trasa `GET /api/u/{handle}/shelf/` | Modify |
| `backend-django/shelf/tests/test_public_shelf.py` | testy publicznej półki | Create |
| `docs/api/openapi.yml` | regeneracja snapshotu kontraktu | Modify (generated) |
| `svelte-frontend/src/lib/api/user.ts` | `listUsers` + typ `UserListItem` | Modify |
| `svelte-frontend/src/lib/api/shelf.ts` | `fetchPublicShelf` | Modify |
| `svelte-frontend/src/lib/components/UserRow.svelte` | opcjonalny `followersCount`, rozluźniony typ | Modify |
| `svelte-frontend/src/routes/users/+page.server.ts` | SSR load listy | Create |
| `svelte-frontend/src/routes/users/+page.svelte` | UI listy (search/ordering/load-more) | Create |
| `svelte-frontend/src/routes/u/[handle]/+page.server.ts` | dołożenie `fetchPublicShelf` | Modify |
| `svelte-frontend/src/routes/u/[handle]/+page.svelte` | sekcja „Reading" | Modify |
| `svelte-frontend/src/lib/components/shell/AppShell.svelte` | link „People" | Modify |
| `svelte-frontend/e2e/users.spec.ts` | E2E discovery | Create |

---

## Task 1: Backend — `GET /api/users/` lista publicznych profili

**Files:**
- Modify: `backend-django/users/serializers.py`
- Modify: `backend-django/users/views.py`
- Modify: `backend-django/users/urls/users.py`
- Test: `backend-django/users/tests/test_user_list.py`

- [ ] **Step 1: Write the failing tests**

Create `backend-django/users/tests/test_user_list.py`:

```python
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from users.models import User, UserFollow


class UserListViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.alice = User.objects.create_user(
            email="alice@test.com", handle="alice", password="pass123",
            display_name="Alice A", profile_public=True,
        )
        self.bob = User.objects.create_user(
            email="bob@test.com", handle="bob", password="pass123",
            display_name="Bob B", profile_public=True,
        )
        self.hidden = User.objects.create_user(
            email="hidden@test.com", handle="hidden", password="pass123",
            profile_public=False,
        )
        # Alice is followed by Bob -> followers_count=1, used for default ordering.
        UserFollow.objects.create(follower=self.bob, following=self.alice)

    def test_lists_only_public_profiles(self):
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        handles = [u["handle"] for u in response.data["data"]]
        self.assertIn("alice", handles)
        self.assertIn("bob", handles)
        self.assertNotIn("hidden", handles)

    def test_pagination_envelope_shape(self):
        response = self.client.get("/api/users/")
        self.assertEqual(set(response.data.keys()), {"data", "page", "per_page", "total"})
        self.assertEqual(response.data["total"], 2)

    def test_default_ordering_most_followed_first(self):
        response = self.client.get("/api/users/")
        handles = [u["handle"] for u in response.data["data"]]
        # Alice has 1 follower, Bob has 0 -> Alice first.
        self.assertEqual(handles[0], "alice")

    def test_ordering_by_newest(self):
        response = self.client.get("/api/users/?ordering=-created_at")
        handles = [u["handle"] for u in response.data["data"]]
        # hidden is newest but private; among public, bob created after alice.
        self.assertEqual(handles[0], "bob")

    def test_search_by_handle(self):
        response = self.client.get("/api/users/?search=ali")
        handles = [u["handle"] for u in response.data["data"]]
        self.assertEqual(handles, ["alice"])

    def test_search_by_display_name(self):
        response = self.client.get("/api/users/?search=Bob B")
        handles = [u["handle"] for u in response.data["data"]]
        self.assertEqual(handles, ["bob"])

    def test_followers_count_in_payload(self):
        response = self.client.get("/api/users/?search=alice")
        self.assertEqual(response.data["data"][0]["followers_count"], 1)

    def test_anonymous_access_allowed(self):
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd backend-django && DJANGO_ENV=dev DATABASE_URL='postgres://postgres:CHANGE_ME@localhost:5432/booksdb' uv run python manage.py test users.tests.test_user_list -v 2
```
Expected: FAIL (404 — route not defined yet).

- [ ] **Step 3: Add `UserListSerializer`**

In `backend-django/users/serializers.py`, append after `UserProfileSerializer` (before `UserSettingsPatchSerializer`):

```python
class UserListSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    followers_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = ("handle", "display_name", "avatar_url", "followers_count")

    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.avatar.url) if request else obj.avatar.url
        return None
```

- [ ] **Step 4: Add `UserListView`**

In `backend-django/users/views.py`:

Add to the `rest_framework` import line (line 11) `filters`:
```python
from rest_framework import filters, generics, permissions, serializers, status, views
```

Add `UserListSerializer` to the `users.serializers` import block (lines 22-36).

Add `from config.pagination import StandardPagination` near the other top imports.

Add the view (e.g. right after `UserProfileView`):
```python
class UserListView(generics.ListAPIView):
    """Public, paginated list of public profiles. Search by handle/display_name;
    order by follower count (default) or recency."""

    permission_classes = (permissions.AllowAny,)
    serializer_class = UserListSerializer
    pagination_class = StandardPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("handle", "display_name")
    ordering_fields = ("followers_count", "created_at")
    ordering = ("-followers_count", "handle")

    def get_queryset(self):
        return User.objects.filter(profile_public=True).annotate(
            followers_count=Count("follower_set", distinct=True)
        )
```

(`Count` is already imported at line 7.)

- [ ] **Step 5: Wire the route**

In `backend-django/users/urls/users.py`, add `UserListView` to the import and a root path:
```python
from users.views import (
    AvatarUploadView,
    DataExportView,
    EmailChangeView,
    MyStatsView,
    PasswordChangeView,
    UserListView,
    UserMeView,
    UserSettingsView,
)

urlpatterns = [
    path("", UserListView.as_view()),
    path("me/", UserMeView.as_view()),
    path("me/password/", PasswordChangeView.as_view()),
    path("me/email/", EmailChangeView.as_view()),
    path("me/avatar/", AvatarUploadView.as_view()),
    path("me/settings/", UserSettingsView.as_view()),
    path("me/export/", DataExportView.as_view()),
    path("me/stats/", MyStatsView.as_view()),
]
```
(`""` matches `/api/users/`; the literal `me/...` paths are unaffected.)

- [ ] **Step 6: Run tests to verify they pass**

Run:
```bash
cd backend-django && DJANGO_ENV=dev DATABASE_URL='postgres://postgres:CHANGE_ME@localhost:5432/booksdb' uv run python manage.py test users.tests.test_user_list -v 2
```
Expected: PASS (8 tests).

- [ ] **Step 7: Lint**

Run: `cd backend-django && uv run ruff check users/`
Expected: no errors.

- [ ] **Step 8: Commit**

```bash
git add backend-django/users/serializers.py backend-django/users/views.py backend-django/users/urls/users.py backend-django/users/tests/test_user_list.py
git commit -m "feat: add public user list endpoint"
```

---

## Task 2: Backend — `GET /api/u/{handle}/shelf/` publiczna domyślna półka

**Files:**
- Modify: `backend-django/shelf/serializers.py`
- Modify: `backend-django/shelf/views.py`
- Modify: `backend-django/config/urls.py`
- Test: `backend-django/shelf/tests/test_public_shelf.py`

- [ ] **Step 1: Write the failing tests**

Create `backend-django/shelf/tests/test_public_shelf.py`:

```python
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from ratings.models import Rating
from shelf.models import ShelfEntry
from users.models import User


class PublicShelfEntryListViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            email="owner@test.com", handle="reader", password="pass123",
            profile_public=True,
        )
        self.visitor = User.objects.create_user(
            email="visitor@test.com", handle="visitor", password="pass123",
        )
        self.book_a = Book.objects.create(title="Book A", slug="book-a")
        self.book_b = Book.objects.create(title="Book B", slug="book-b")
        # book_b added later -> should sort first (-created_at).
        ShelfEntry.objects.create(user=self.owner, book=self.book_a, status="READ")
        ShelfEntry.objects.create(user=self.owner, book=self.book_b, status="READING")
        Rating.objects.create(user=self.owner, book=self.book_a, rating=5)

    def test_returns_all_owner_entries(self):
        response = self.client.get(f"/api/u/{self.owner.handle}/shelf/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_ordered_newest_first(self):
        response = self.client.get(f"/api/u/{self.owner.handle}/shelf/")
        slugs = [e["book"]["slug"] for e in response.data]
        self.assertEqual(slugs, ["book-b", "book-a"])

    def test_includes_owner_rating(self):
        response = self.client.get(f"/api/u/{self.owner.handle}/shelf/")
        by_slug = {e["book"]["slug"]: e for e in response.data}
        self.assertEqual(by_slug["book-a"]["user_rating"], 5)
        self.assertIsNone(by_slug["book-b"]["user_rating"])

    def test_entry_exposes_status_and_dates(self):
        response = self.client.get(f"/api/u/{self.owner.handle}/shelf/")
        entry = response.data[0]
        self.assertEqual(
            set(entry.keys()),
            {"status", "start_date", "finish_date", "current_page", "user_rating", "book"},
        )

    def test_private_profile_404_for_visitor(self):
        self.owner.profile_public = False
        self.owner.save()
        self.client.force_authenticate(user=self.visitor)
        response = self.client.get(f"/api/u/{self.owner.handle}/shelf/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_private_profile_owner_sees_own(self):
        self.owner.profile_public = False
        self.owner.save()
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f"/api/u/{self.owner.handle}/shelf/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_nonexistent_handle_404(self):
        response = self.client.get("/api/u/ghost/shelf/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd backend-django && DJANGO_ENV=dev DATABASE_URL='postgres://postgres:CHANGE_ME@localhost:5432/booksdb' uv run python manage.py test shelf.tests.test_public_shelf -v 2
```
Expected: FAIL (404 — route not defined).

- [ ] **Step 3: Add `PublicShelfEntrySerializer`**

In `backend-django/shelf/serializers.py`, append at the end of the file:

```python
class PublicShelfEntrySerializer(serializers.ModelSerializer):
    """Read-only view of another user's reading entry (M11)."""

    book = ShelfBookSerializer(read_only=True)
    user_rating = serializers.SerializerMethodField()

    class Meta:
        model = ShelfEntry
        fields = ["status", "start_date", "finish_date", "current_page", "user_rating", "book"]

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_user_rating(self, obj):
        # Populated by the view's Subquery annotation; absent -> None.
        return getattr(obj, "user_rating", None)
```

(`ShelfBookSerializer`, `extend_schema_field`, `ShelfEntry` are already imported at the top.)

- [ ] **Step 4: Add `PublicShelfEntryListView`**

In `backend-django/shelf/views.py`, add `PublicShelfEntrySerializer` to the `.serializers` import block, then append at the end of the file:

```python
class PublicShelfEntryListView(generics.ListAPIView):
    """Another user's default reading shelf (all statuses), gated by profile_public."""

    permission_classes = [AllowAny]
    serializer_class = PublicShelfEntrySerializer
    pagination_class = None

    def get_queryset(self):
        owner = _public_owner_or_404(self.request, self.kwargs["handle"])
        user_rating = Rating.objects.filter(
            user=OuterRef("user"), book=OuterRef("book")
        ).values("rating")[:1]
        return (
            ShelfEntry.objects.filter(user=owner)
            .annotate(user_rating=Subquery(user_rating))
            .select_related("book")
            .prefetch_related("book__authors", "book__genres")
            .order_by("-created_at")
        )
```

(`generics`, `AllowAny`, `OuterRef`, `Subquery`, `Rating`, `ShelfEntry`, `_public_owner_or_404` are already present in this module.)

- [ ] **Step 5: Wire the route**

In `backend-django/config/urls.py`, add the import and path. Add near the top with the other imports:
```python
from shelf.views import PublicShelfEntryListView
```
Add this line directly above the existing `path("api/u/<str:handle>/shelves/", ...)` line:
```python
    path("api/u/<str:handle>/shelf/", PublicShelfEntryListView.as_view()),
```

- [ ] **Step 6: Run tests to verify they pass**

Run:
```bash
cd backend-django && DJANGO_ENV=dev DATABASE_URL='postgres://postgres:CHANGE_ME@localhost:5432/booksdb' uv run python manage.py test shelf.tests.test_public_shelf -v 2
```
Expected: PASS (7 tests).

- [ ] **Step 7: Lint**

Run: `cd backend-django && uv run ruff check shelf/ config/`
Expected: no errors.

- [ ] **Step 8: Commit**

```bash
git add backend-django/shelf/serializers.py backend-django/shelf/views.py backend-django/config/urls.py backend-django/shelf/tests/test_public_shelf.py
git commit -m "feat: add public reading shelf endpoint"
```

---

## Task 3: Regenerate OpenAPI snapshot

**Files:**
- Modify: `docs/api/openapi.yml` (generated)

- [ ] **Step 1: Run the contract test to confirm it now fails**

Run:
```bash
cd backend-django && DJANGO_ENV=dev DATABASE_URL='postgres://postgres:CHANGE_ME@localhost:5432/booksdb' uv run python manage.py test config.tests.test_openapi_schema -v 2
```
Expected: FAIL (snapshot is missing the two new paths).

- [ ] **Step 2: Regenerate the snapshot**

Run: `make regenerate-openapi`
Expected: `docs/api/openapi.yml` updated with `/api/users/` and `/api/u/{handle}/shelf/`.

- [ ] **Step 3: Run the contract test to confirm it passes**

Run:
```bash
cd backend-django && DJANGO_ENV=dev DATABASE_URL='postgres://postgres:CHANGE_ME@localhost:5432/booksdb' uv run python manage.py test config.tests.test_openapi_schema -v 2
```
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add docs/api/openapi.yml
git commit -m "docs: regenerate openapi for M11 endpoints"
```

---

## Task 4: Frontend — API clients

**Files:**
- Modify: `svelte-frontend/src/lib/api/user.ts`
- Modify: `svelte-frontend/src/lib/api/shelf.ts`

- [ ] **Step 1: Add `listUsers` + `UserListItem` to `user.ts`**

Replace the contents of `svelte-frontend/src/lib/api/user.ts` with:

```typescript
import { apiFetch } from './_client';
import type { PaginatedResponse } from './books';

export interface UserMe {
	id: number;
	handle: string;
	display_name: string;
	email: string;
	bio: string | null;
	avatar_url: string | null;
	member_since: string;
	profile_public: boolean;
}

export async function getCurrentUser(fetchFn: typeof fetch) {
	return apiFetch<UserMe>(fetchFn, '/users/me/', undefined, true);
}

export interface UserListItem {
	handle: string;
	display_name: string;
	avatar_url: string | null;
	followers_count: number;
}

export interface ListUsersParams {
	search?: string;
	ordering?: string;
	page?: number;
	perPage?: number;
}

export async function listUsers(
	fetchFn: typeof fetch,
	params: ListUsersParams = {},
	isServerSide = false
) {
	const sp = new URLSearchParams();
	if (params.search) sp.set('search', params.search);
	if (params.ordering) sp.set('ordering', params.ordering);
	if (params.page) sp.set('page', String(params.page));
	if (params.perPage) sp.set('per_page', String(params.perPage));
	const qs = sp.toString();
	return apiFetch<PaginatedResponse<UserListItem>>(
		fetchFn,
		`/users/${qs ? `?${qs}` : ''}`,
		undefined,
		isServerSide
	);
}
```

- [ ] **Step 2: Add `fetchPublicShelf` to `shelf.ts`**

In `svelte-frontend/src/lib/api/shelf.ts`, append after `fetchShelfEntries`:

```typescript
/** Another user's public default reading shelf (M11). */
export function fetchPublicShelf(fetchFn: typeof fetch, handle: string, isServerSide = false) {
	return apiFetch<ShelfEntry[]>(fetchFn, `/u/${handle}/shelf/`, undefined, isServerSide);
}
```

- [ ] **Step 3: Type-check**

Run: `cd svelte-frontend && npm run check`
Expected: 0 errors.

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/src/lib/api/user.ts svelte-frontend/src/lib/api/shelf.ts
git commit -m "feat: add listUsers and fetchPublicShelf clients"
```

---

## Task 5: Frontend — extend `UserRow`

**Files:**
- Modify: `svelte-frontend/src/lib/components/UserRow.svelte`

- [ ] **Step 1: Relax the type and add optional `followersCount`**

Replace the contents of `svelte-frontend/src/lib/components/UserRow.svelte` with:

```svelte
<script lang="ts">
	import Avatar from '$lib/components/Avatar.svelte';

	// Structural type = common subset of FollowUser and UserListItem, so this row
	// is reusable by followers/following lists (no count) and /users (with count).
	let {
		user,
		followersCount
	}: {
		user: { handle: string; display_name: string; avatar_url: string | null };
		followersCount?: number;
	} = $props();
</script>

<a
	href="/u/{user.handle}"
	class="flex items-center gap-3 rounded-lg border border-rule bg-surface px-4 py-3 hover:bg-paper-2 transition-colors"
>
	<Avatar name={user.display_name || user.handle} avatarUrl={user.avatar_url} size="md" />
	<div class="min-w-0">
		<p class="text-ink font-medium truncate">{user.display_name || user.handle}</p>
		<p class="text-sm text-muted truncate">@{user.handle}</p>
	</div>
	{#if followersCount !== undefined}
		<span class="ml-auto shrink-0 text-sm text-muted">{followersCount} followers</span>
	{/if}
</a>
```

- [ ] **Step 2: Type-check (verify FollowList still compiles)**

Run: `cd svelte-frontend && npm run check`
Expected: 0 errors (FollowList passes `FollowUser`, assignable to the relaxed type).

- [ ] **Step 3: Commit**

```bash
git add svelte-frontend/src/lib/components/UserRow.svelte
git commit -m "feat: optional followers count in UserRow"
```

---

## Task 6: Frontend — `/users` route

**Files:**
- Create: `svelte-frontend/src/routes/users/+page.server.ts`
- Create: `svelte-frontend/src/routes/users/+page.svelte`

- [ ] **Step 1: Create the SSR loader**

Create `svelte-frontend/src/routes/users/+page.server.ts`:

```typescript
import type { PageServerLoad } from './$types';
import { listUsers } from '$lib/api/user';

export const load: PageServerLoad = async ({ fetch, url }) => {
	const search = url.searchParams.get('search') ?? '';
	const ordering = url.searchParams.get('ordering') ?? '-followers_count';

	const { data, error } = await listUsers(
		fetch,
		{ search: search || undefined, ordering, page: 1, perPage: 20 },
		true
	);

	return {
		initialUsers: data?.data ?? [],
		initialTotal: data?.total ?? 0,
		initialSearch: search,
		initialOrdering: ordering,
		loadError: error ? { status: error.status, detail: error.detail } : null
	};
};
```

- [ ] **Step 2: Create the page**

Create `svelte-frontend/src/routes/users/+page.svelte`:

```svelte
<script lang="ts">
	import UserRow from '$lib/components/UserRow.svelte';
	import { Button } from '$lib/components/ui/button';
	import { listUsers, type UserListItem } from '$lib/api/user';

	let { data } = $props();

	let users = $state<UserListItem[]>(data.initialUsers);
	let total = $state<number>(data.initialTotal);
	let search = $state<string>(data.initialSearch);
	let ordering = $state<string>(data.initialOrdering);
	let currentPage = $state(1);
	let loading = $state(false);

	const hasMore = $derived(users.length < total);
	const PER_PAGE = 20;

	let debounce: ReturnType<typeof setTimeout> | undefined;

	async function reload() {
		loading = true;
		const { data: page } = await listUsers(fetch, {
			search: search || undefined,
			ordering,
			page: 1,
			perPage: PER_PAGE
		});
		users = page?.data ?? [];
		total = page?.total ?? 0;
		currentPage = 1;
		loading = false;
	}

	function onSearchInput() {
		clearTimeout(debounce);
		debounce = setTimeout(reload, 250);
	}

	function setOrdering(value: string) {
		if (ordering === value) return;
		ordering = value;
		reload();
	}

	async function loadMore() {
		loading = true;
		const next = currentPage + 1;
		const { data: page } = await listUsers(fetch, {
			search: search || undefined,
			ordering,
			page: next,
			perPage: PER_PAGE
		});
		users = [...users, ...(page?.data ?? [])];
		total = page?.total ?? total;
		currentPage = next;
		loading = false;
	}
</script>

<svelte:head>
	<title>People — Storyshelf</title>
</svelte:head>

<div class="max-w-[1240px] mx-auto px-6 md:px-10 py-8 space-y-6">
	<h1 class="font-display text-2xl font-semibold text-ink">People</h1>

	<div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
		<input
			type="search"
			placeholder="Search people"
			bind:value={search}
			oninput={onSearchInput}
			class="w-full sm:max-w-xs rounded-lg border border-rule bg-surface px-3 py-2 text-ink"
		/>
		<div class="flex gap-1">
			<Button
				variant={ordering === '-followers_count' ? 'default' : 'ghost'}
				size="sm"
				onclick={() => setOrdering('-followers_count')}
			>
				Most followed
			</Button>
			<Button
				variant={ordering === '-created_at' ? 'default' : 'ghost'}
				size="sm"
				onclick={() => setOrdering('-created_at')}
			>
				Newest
			</Button>
		</div>
	</div>

	{#if users.length === 0}
		<p class="text-muted text-sm">No people found.</p>
	{:else}
		<ul class="flex flex-col gap-2">
			{#each users as u (u.handle)}
				<li><UserRow user={u} followersCount={u.followers_count} /></li>
			{/each}
		</ul>
	{/if}

	{#if hasMore}
		<div class="flex justify-center">
			<Button variant="outline" size="sm" disabled={loading} onclick={loadMore}>
				{loading ? 'Loading…' : 'Load more'}
			</Button>
		</div>
	{/if}
</div>
```

- [ ] **Step 3: Type-check + lint**

Run: `cd svelte-frontend && npm run check && npm run lint`
Expected: 0 errors.

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/src/routes/users/
git commit -m "feat: add /users discovery page"
```

---

## Task 7: Frontend — „Reading" section on profile

**Files:**
- Modify: `svelte-frontend/src/routes/u/[handle]/+page.server.ts`
- Modify: `svelte-frontend/src/routes/u/[handle]/+page.svelte`

- [ ] **Step 1: Load the public shelf**

In `svelte-frontend/src/routes/u/[handle]/+page.server.ts`, add the import and fetch. Updated file:

```typescript
import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { apiFetch } from '$lib/api/_client';
import { fetchPublicShelves } from '$lib/api/shelves';
import { fetchPublicShelf } from '$lib/api/shelf';
import type { User } from '$lib/types';

export const load: PageServerLoad = async ({ fetch, params, parent }) => {
	const { data: profile, error: profileErr } = await apiFetch<User>(
		fetch,
		`/u/${params.handle}/`,
		undefined,
		true
	);
	if (profileErr) {
		throw error(profileErr.status === 404 ? 404 : 500, profileErr.detail);
	}

	const { user: viewer } = await parent();
	const isOwner = viewer?.handle === params.handle;
	const isLoggedIn = !!viewer;

	const { data: shelves } = await fetchPublicShelves(fetch, params.handle, true);
	const { data: reading } = await fetchPublicShelf(fetch, params.handle, true);

	return { profile, isOwner, isLoggedIn, shelves: shelves ?? [], reading: reading ?? [] };
};
```

- [ ] **Step 2: Render the section**

In `svelte-frontend/src/routes/u/[handle]/+page.svelte`:

Add to the script block (after the `shelves` derived, line ~14) the imports/derived:
```typescript
	import type { ShelfEntry } from '$lib/types/shelf';
	let reading: ShelfEntry[] = $derived(data.reading);

	const STATUS_LABEL: Record<string, string> = {
		WANT_TO_READ: 'Want to read',
		READING: 'Reading',
		READ: 'Read'
	};
```

Add the section directly after the existing `{#if shelves.length > 0}...{/if}` block (before the closing `</div>`):
```svelte
	{#if reading.length > 0}
		<section class="mt-10">
			<h2 class="font-display text-xl font-medium text-ink mb-4">Reading</h2>
			<ul class="flex flex-col gap-2">
				{#each reading as entry (entry.book.slug)}
					<li>
						<a
							href="/books/{entry.book.slug}"
							class="flex items-center gap-3 rounded-lg border border-rule bg-surface px-4 py-3 hover:bg-paper-2 transition-colors"
						>
							{#if entry.book.cover_url}
								<img
									src={entry.book.cover_url}
									alt=""
									class="h-12 w-8 shrink-0 rounded object-cover"
								/>
							{/if}
							<div class="min-w-0 flex-1">
								<p class="text-ink font-medium truncate">{entry.book.title}</p>
								<p class="text-sm text-muted truncate">{entry.book.authors.join(', ')}</p>
							</div>
							{#if entry.user_rating}
								<span class="shrink-0 text-sm text-muted">★ {entry.user_rating}</span>
							{/if}
							<span
								class="shrink-0 rounded-full border border-rule px-2 py-0.5 text-xs text-muted"
							>
								{STATUS_LABEL[entry.status]}
							</span>
						</a>
					</li>
				{/each}
			</ul>
		</section>
	{/if}
```

- [ ] **Step 3: Type-check + lint**

Run: `cd svelte-frontend && npm run check && npm run lint`
Expected: 0 errors.

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/src/routes/u/[handle]/+page.server.ts svelte-frontend/src/routes/u/[handle]/+page.svelte
git commit -m "feat: show reading shelf on public profile"
```

---

## Task 8: Frontend — „People" nav link

**Files:**
- Modify: `svelte-frontend/src/lib/components/shell/AppShell.svelte`

- [ ] **Step 1: Add the nav link**

In `svelte-frontend/src/lib/components/shell/AppShell.svelte`, in the `<nav>` block, add a People link after the Discover button (visible to everyone — endpoint is public):

```svelte
				<nav class="hidden md:flex items-center gap-1">
					<Button variant="ghost" size="sm" href={resolve('/discover')}>Discover</Button>
					<Button variant="ghost" size="sm" href={resolve('/users')}>People</Button>
					{#if user}
						<Button variant="ghost" size="sm" href={resolve('/shelf')}>Shelf</Button>
						<Button variant="ghost" size="sm" href={resolve('/stats')}>Stats</Button>
					{/if}
				</nav>
```

- [ ] **Step 2: Type-check**

Run: `cd svelte-frontend && npm run check`
Expected: 0 errors. (If `resolve('/users')` fails typegen because the route is new, run `npm run check` again after Task 6 created the route — it should already exist.)

- [ ] **Step 3: Commit**

```bash
git add svelte-frontend/src/lib/components/shell/AppShell.svelte
git commit -m "feat: add People link to nav"
```

---

## Task 9: E2E — `users.spec.ts`

**Files:**
- Create: `svelte-frontend/e2e/users.spec.ts`

Note: `page.request` with a relative `/api/...` URL hits the frontend origin, which proxies to Django (ADR-002 same-origin `/api`), carrying the HttpOnly auth cookies from the browser context — the same path the app uses. The logged-in `authUser` is made public and given a reading entry, then appears in their own `/users` results (self is not special-cased).

- [ ] **Step 1: Write the spec**

Create `svelte-frontend/e2e/users.spec.ts`:

```typescript
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { test, expect } from './fixtures';

const slugsPath = resolve(__dirname, '.seed-slugs.json');
let slugs: Record<string, string>;
try {
	slugs = JSON.parse(readFileSync(slugsPath, 'utf-8'));
} catch {
	throw new Error('Missing .seed-slugs.json — run global setup first.');
}
const duneSlug = slugs['Dune'];

test.describe('User discovery', () => {
	test('public user appears in /users, search filters, profile shows Reading', async ({
		page,
		authUser
	}) => {
		// Make the logged-in user public and put a book on their reading shelf.
		const settingsRes = await page.request.patch('/api/users/me/settings/', {
			data: { profile_public: true }
		});
		expect(settingsRes.ok()).toBeTruthy();
		const shelfRes = await page.request.post('/api/shelf/entries/', {
			data: { book_slug: duneSlug, status: 'READING' }
		});
		expect(shelfRes.ok()).toBeTruthy();

		// Discover list: search by handle finds the user.
		await page.goto('/users');
		await page.waitForLoadState('networkidle');
		await page.getByPlaceholder('Search people').fill(authUser.handle);
		await expect(page.getByText(`@${authUser.handle}`)).toBeVisible();

		// Click through to the profile and see the Reading section + the book.
		await page.getByText(`@${authUser.handle}`).click();
		await expect(page.getByRole('heading', { name: 'Reading' })).toBeVisible();
		await expect(page.getByText('Dune')).toBeVisible();
	});

	test('search with no match shows no rows', async ({ page, authUser }) => {
		await page.request.patch('/api/users/me/settings/', { data: { profile_public: true } });
		await page.goto('/users');
		await page.waitForLoadState('networkidle');
		await page.getByPlaceholder('Search people').fill('zzzznomatchzzzz');
		await expect(page.getByText(`@${authUser.handle}`)).toHaveCount(0);
	});
});
```

- [ ] **Step 2: Run the E2E spec**

Ensure the dev stack is up (`make dev-up`), then:
```bash
cd svelte-frontend && npx playwright test users.spec.ts
```
Expected: 2 passed. (If registration throttling blocks fixtures — 5 registrations/hour — reset with `docker restart storyshelf-django` and re-run.)

- [ ] **Step 3: Commit**

```bash
git add svelte-frontend/e2e/users.spec.ts
git commit -m "test: e2e for user discovery"
```

---

## Final verification

- [ ] **Backend full suite**

Run:
```bash
cd backend-django && DJANGO_ENV=dev DATABASE_URL='postgres://postgres:CHANGE_ME@localhost:5432/booksdb' uv run python manage.py test
```
Expected: all green (existing + ~15 new).

- [ ] **Backend lint**

Run: `cd backend-django && uv run ruff check .`
Expected: no errors.

- [ ] **Frontend check + lint**

Run: `cd svelte-frontend && npm run check && npm run lint`
Expected: 0 errors.

- [ ] **Then:** use superpowers:finishing-a-development-branch to open the PR.
