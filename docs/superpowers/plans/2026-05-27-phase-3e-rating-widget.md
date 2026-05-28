# Phase 3e: RatingWidget on /books/[slug] — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add interactive RatingStars component to existing book detail page, next to BookHero (cover + title area). Community average displayed as text label, user's own rating as interactive stars with PUT/DELETE mutations.

**Architecture:** Reuse RatingStars component from 3c. Fetch user's rating server-side in `+page.server.ts` alongside book data (both parallel after `parent()` resolves). Auth-conditional: interactive for logged-in users, display-only for anonymous. Community average shown as text label next to interactive stars.

**Tech Stack:** SvelteKit 2, Svelte 5 runes, Tailwind v4, TypeScript, svelte-sonner (toast).

**Prerequisites (MUST be complete before starting):**
- **M2 Phase 2d** — `/books/[slug]` route, `+page.server.ts`, `+page.svelte`, `+error.svelte`, `getBook()` in `$lib/api/book.ts`, updated `Book` type
- **M3 Phase 3a** — Rating API (`/api/ratings/` endpoint with PUT upsert, GET list, DELETE)
- **M3 Phase 3c** — `RatingStars.svelte` with props: `rating: number | null`, `onRate: (star: number) => Promise<void>`, `readonly?: boolean`, `size?: 'sm' | 'md'` (star value is always 1-5, toggle logic in page handler)

> **If 3c hasn't added `onRate` and `rating` props to RatingStars yet:** Task 3 below includes the exact changes needed. The existing component only has `value` (bindable), `readonly`, and `size`. This plan assumes the component will be enhanced — either by 3c or by Task 3 here.

---

## Pre-flight: verify current state

- [ ] **Step 1: Confirm the book detail route exists**

```bash
test -f svelte-frontend/src/routes/books/\[slug\]/+page.svelte && echo "OK" || echo "MISSING — run Phase 2d first"
test -f svelte-frontend/src/routes/books/\[slug\]/+page.server.ts && echo "OK" || echo "MISSING — run Phase 2d first"
```
Expected: both `OK`

- [ ] **Step 2: Verify RatingStars component exists**

```bash
test -f svelte-frontend/src/lib/components/book/RatingStars.svelte && echo "OK" || echo "MISSING"
```
Expected: `OK`

- [ ] **Step 3: Verify API layer has getBook**

```bash
grep "getBook" svelte-frontend/src/lib/api/book.ts
```
Expected: function signature found.

- [ ] **Step 4: Check current RatingStars props**

```bash
grep -A2 "interface Props" svelte-frontend/src/lib/components/book/RatingStars.svelte
```
This tells us whether 3c has already added `onRate` and `rating` props, or if Task 3 must add them.

---

## Task 1: Create ratings API client

**File:** Add to existing: `svelte-frontend/src/lib/api/ratings.ts`

> Phase 3c already created `ratings.ts` with `RatingResponse`, `fetchRatings`, `upsertRating`, `deleteRatingById`. This phase adds `fetchUserRating` to the same file — no duplication.

Add `fetchUserRating` (server-side, takes `fetchFn`), reusing the `RatingResponse` interface from 3c. The existing `upsertRating` and `deleteRatingById` are reused directly.

- [ ] **Step 1: Add `fetchUserRating` to `svelte-frontend/src/lib/api/ratings.ts`**

Append this function to the existing file:

```typescript
/**
 * Fetch the current user's rating for a specific book.
 * Returns null if the user hasn't rated the book, or the Rating object.
 * Intended for server-side use (pass SvelteKit SSR fetch).
 */
export async function fetchUserRating(
	fetchFn: typeof fetch,
	bookSlug: string
): Promise<{ data: RatingResponse | null; error: ApiError | null }> {
	const { data, error } = await apiFetch<RatingResponse[]>(
		fetchFn,
		`/ratings/?book_slug=${encodeURIComponent(bookSlug)}`
	);
	if (error) return { data: null, error };
	// The endpoint returns a list filtered by book_slug (0 or 1 element)
	return { data: data?.[0] ?? null, error: null };
}
```

Design decisions:
- `fetchUserRating` returns `RatingResponse | null` — simplifies callers (don't need to check `data?.[0]`)
- Uses `RatingResponse` interface (already defined in `ratings.ts` by 3c) — same shape
- `fetchFn` parameter allows SSR (SvelteKit fetch with cookie forwarding) and client-side (browser fetch with `credentials: 'include'`)

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd svelte-frontend && npx tsc --noEmit src/lib/api/ratings.ts 2>&1 | head -10
```
Expected: no errors (may show warning about `--noEmit` with file path — ignore)

- [ ] **Step 3: Commit**

```bash
git add svelte-frontend/src/lib/api/ratings.ts
git commit -m "feat(api): add fetchUserRating to ratings API client"
```

---

## Task 2: Update `+page.server.ts` — pass user and fetch rating

**File:** Modify: `svelte-frontend/src/routes/books/[slug]/+page.server.ts`

Extends the existing server load (created in Phase 2d) to:
1. Extract `user` from `parent()` (the root `+layout.server.ts` calls `getCurrentUser(fetch)` and returns `{ user }`)
2. Fetch the user's rating for this book (only if authenticated)
3. Run `getBook` and `fetchUserRating` in parallel after `parent()` resolves
4. Return `{ book, user, userRating }`

- [ ] **Step 1: Replace the file content**

```typescript
import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { getBook } from '$lib/api/book';
import { fetchUserRating } from '$lib/api/ratings';

export const load: PageServerLoad = async ({ params, fetch, parent }) => {
	const { user } = await parent();

	// Fetch book and user rating in parallel (if authenticated)
	const [bookResult, ratingResult] = await Promise.all([
		getBook(fetch, params.slug),
		user ? fetchUserRating(fetch, params.slug) : Promise.resolve({ data: null, error: null }),
	]);

	const { data: book, error: apiError } = bookResult;
	if (apiError?.status === 404 || !book) {
		throw error(404, 'Book not found');
	}
	if (apiError) {
		throw error(apiError.status, apiError.detail);
	}

	const { data: rating } = ratingResult;
	// rating fetch failure is non-fatal — show page without user rating
	const userRating = rating ? { rating: rating.rating, id: rating.id } : null;

	return { book, user, userRating };
};
```

Data flow:
1. `parent()` resolves the root layout's `{ user, authError }` — user is `UserMe | null`
2. `Promise.all` runs `getBook` + `fetchUserRating` concurrently (if user is authenticated, otherwise ratingResult resolves immediately with null)
3. Book 404/error → throw → `+error.svelte` handles it (unchanged from Phase 2d)
4. Rating fetch failure → non-fatal, `userRating` stays null
5. Successful rating fetch → extract `{ rating, id }` into `userRating`
6. All three values passed to `+page.svelte` as `data`

Changes from Phase 2d server load:
| Before | After |
|--------|-------|
| No user extraction | `const { user } = await parent()` |
| Only `getBook` call | `Promise.all([getBook, fetchUserRating])` |
| Returns `{ book }` | Returns `{ book, user, userRating }` |

- [ ] **Step 2: Type-check the route**

```bash
cd svelte-frontend && npm run check 2>&1 | grep -E "\[slug\]|error" | head -15
```
Expected: no errors for `[slug]` route. May show other pre-existing warnings — ignore.

- [ ] **Step 3: Commit**

```bash
git add svelte-frontend/src/routes/books/\[slug\]/+page.server.ts
git commit -m "feat(books): load user and userRating in book detail server load"
```

---

## Task 3: Ensure RatingStars has required props (onRate + rating)

**File:** Possibly modify: `svelte-frontend/src/lib/components/book/RatingStars.svelte`

> **Skip this task if Pre-flight Step 4 confirms `onRate` and `rating` props already exist (Phase 3c added them).**

The existing RatingStars (created early for M3) has: `value` (bindable number), `readonly` (boolean), `size` (sm/md). For the `/books/[slug]` integration, it needs:
- `rating: number | null` — the current user rating (0 means no rating, displayed as empty stars)
- `onRate: (star: number) => Promise<void>` — async callback called when user clicks a star
- `readonly: boolean` — already exists

The `onRate` callback lets the page component handle the API call (PUT/DELETE) and update state. The component handles click-to-toggle logic: clicking the same star clears the rating.

- [ ] **Step 1: Replace the component script section**

Read the current file first:

```bash
cat svelte-frontend/src/lib/components/book/RatingStars.svelte
```

Then replace the `<script>` block (lines 1–21) while keeping the template (lines 23–45) unchanged:

```svelte
<script lang="ts">
	import { Star } from 'lucide-svelte';

	interface Props {
		/** Current rating value (null = unrated). Parent updates after onRate resolves. */
		rating?: number | null;
		/** Optional async callback. When provided, clicking a star calls this with star value (1-5). */
		onRate?: (star: number) => Promise<void>;
		/** Disable all interaction (display-only). */
		readonly?: boolean;
		/** Star size. */
		size?: 'sm' | 'md';
	}
	let { rating = null, onRate = undefined, readonly = false, size = 'md' }: Props = $props();

	const sizeMap: Record<string, string> = { sm: 'size-3', md: 'size-4' };
	const sizeCls = $derived(sizeMap[size] ?? 'size-4');

	let hoverValue = $state(0);
	let loading = $state(false);

	/** Display value: user's rating or hover preview. */
	const displayValue = $derived(hoverValue > 0 ? hoverValue : (rating ?? 0));

	async function handleClick(star: number) {
		if (readonly || loading || !onRate) return;

		loading = true;
		try {
			await onRate(star); // Always passes 1-5 — toggle logic is in the page handler
		} catch {
			// Caller handles error display (toast)
		} finally {
			loading = false;
		}
	}
</script>
```

Props changes from existing:
| Prop | Before | After |
|------|--------|-------|
| `value` (bindable number, 0–5) | defaults to 0 | → `rating` (number \| null, not bindable) |
| — | — | `onRate?: (star: number) => Promise<void>` — always called with 1-5 |
| — | — | `loading` state (prevents clicks during API call) |

Template changes needed:
The template currently uses `value` for fill checks. Replace with `displayValue`:

- `class:text-accent={star <= value}` → `class:text-accent={star <= displayValue}`
- `class:text-rule={star > value}` → `class:text-rule={star > displayValue}`
- `fill={star <= value ? ...}` → `fill={star <= displayValue ? ...}`
- `disabled={readonly}` → `disabled={readonly || loading}`

No toggle logic inside the component — the component simply calls `onRate(star)` with the clicked star value (1-5). The parent page handler decides whether this means PUT or DELETE based on `star === userRating`.

- [ ] **Step 2: Run svelte-check on the updated component**

```bash
cd svelte-frontend && npm run check 2>&1 | grep "RatingStars" | head -5
```
Expected: no errors for RatingStars.

- [ ] **Step 3: Commit** (skip if no changes needed)

```bash
git add svelte-frontend/src/lib/components/book/RatingStars.svelte
git commit -m "feat(RatingStars): add onRate callback, rating prop, saving state"
```

---

## Task 4: Add RatingStars to `+page.svelte`

**File:** Modify: `svelte-frontend/src/routes/books/[slug]/+page.svelte`

Changes to the book detail page:
1. **Community average** — replace text-only `avg_rating` with numeric value + ratings count as text (no visual stars)
2. **User rating** — add interactive `RatingStars` section between cover and metadata (only if `user` is authenticated)
3. **Mutation handlers** — `handleRate` callback calls `upsertRating` / `deleteRatingById` with browser `fetch`
4. **Loading/error states** — saving state disables stars, errors show toast via `svelte-sonner`
5. **State management** — `userRating` and `ratingId` are reactive local state (initialized from server data)

- [ ] **Step 1: Read the current file for reference**

```bash
cat svelte-frontend/src/routes/books/\[slug\]/+page.svelte
```

- [ ] **Step 2: Replace the file with the enhanced version**

```svelte
<script lang="ts">
	import { page } from '$app/stores';
	import { toast } from 'svelte-sonner';
	import type { PageData } from './$types';
	import BookCover from '$lib/components/book/BookCover.svelte';
	import BookHeader from '$lib/components/book/BookHeader.svelte';
	import BookMeta from '$lib/components/book/BookMeta.svelte';
	import BookDescription from '$lib/components/book/BookDescription.svelte';
	import RatingStars from '$lib/components/book/RatingStars.svelte';
	import { upsertRating, deleteRatingById } from '$lib/api/ratings';

	let { data }: { data: PageData } = $props();

	// Local user rating state (initialized from server data, mutated by user actions).
	let userRating = $state(data.userRating?.rating ?? null);
	let ratingId = $state(data.userRating?.id ?? null);
	let saving = $state(false);

	async function handleRate(star: number) {
		if (saving) return;

		// Toggle: same star → DELETE, different star → PUT upsert
		if (star === userRating && ratingId) {
			saving = true;
			const { error } = await deleteRatingById(fetch, ratingId);
			if (error) {
				toast.error('Failed to remove rating. Try again.');
			} else {
				userRating = null;
				ratingId = null;
			}
			saving = false;
		} else if (star !== userRating) {
			saving = true;
			const { data: result, error } = await upsertRating(fetch, data.book.slug, star);
			if (error) {
				toast.error('Failed to save rating. Try again.');
			} else if (result) {
				userRating = result.rating;
				ratingId = result.id;
			}
			saving = false;
		}
	}
</script>

<svelte:head>
	<title>{data.book.title} — StoryShelf</title>
	<meta name="description" content={data.book.description ?? `Details for ${data.book.title}`} />
	{#if data.book.cover_url}
		<meta property="og:image" content={data.book.cover_url} />
	{/if}
	<meta property="og:title" content={data.book.title} />
</svelte:head>

<div class="max-w-[1240px] mx-auto px-6 md:px-10 py-8">
	<div class="flex flex-col md:flex-row gap-8 md:gap-10">
		<!-- Desktop cover + community rating (hidden on mobile) -->
		<div class="flex-shrink-0 hidden md:flex flex-col items-center gap-3">
			<BookCover coverUrl={data.book.cover_url} title={data.book.title} size="lg" />
			{#if data.book.avg_rating > 0}
				<div class="flex items-baseline gap-1">
					<span class="text-lg font-medium text-ink">{data.book.avg_rating.toFixed(2)}</span>
					<span class="text-xs text-muted">({data.book.ratings_count} rating{data.book.ratings_count !== 1 ? 's' : ''})</span>
				</div>
			{/if}
		</div>

		<!-- Mobile cover + rating (hidden on desktop) -->
		<div class="md:hidden flex flex-col items-center gap-3">
			<BookCover coverUrl={data.book.cover_url} title={data.book.title} size="md" />
			{#if data.book.avg_rating > 0}
				<div class="flex items-baseline gap-1">
					<span class="text-lg font-medium text-ink">{data.book.avg_rating.toFixed(2)}</span>
					<span class="text-xs text-muted">({data.book.ratings_count} rating{data.book.ratings_count !== 1 ? 's' : ''})</span>
				</div>
			{/if}
		</div>

		<!-- Content column -->
		<div class="flex-1 min-w-0 space-y-6">
			<BookHeader book={data.book} />

			<!-- User rating widget (auth only) -->
			{#if data.user}
				<div class="flex items-center gap-3 {saving ? 'opacity-50' : ''}">
					<RatingStars rating={userRating} onRate={handleRate} size="md" />
					<span class="text-sm text-muted">
						{#if userRating}
							Your rating: {userRating}
						{:else}
							Rate this book
						{/if}
					</span>
				</div>
			{/if}

			<BookMeta book={data.book} />
			<BookDescription description={data.book.description} />
		</div>
	</div>
</div>
```

Design decisions:
- **Community average** displayed as text: numeric value and count. Example: `"4.52 (123 ratings)"`. No visual stars — the interactive RatingStars is for the USER's rating only.
- **User rating widget** placed between `BookHeader` and `BookMeta`. Only rendered when `data.user` is truthy.
- **`saving` state** disables interaction (opacity-50 on container, `loading` flag in RatingStars prevents double-clicks). Since the container fades during save, the browser's built-in cursor:wait provides additional feedback.
- **Toggle behavior**: RatingStars always calls `onRate(star)` with a 1-5 value. The `handleRate` callback checks `star === userRating` — if same, DELETE; if different, PUT upsert. This keeps the component dumb and the toggle logic in the page handler.
- **Mutation uses browser `fetch`** (not SSR fetch) — the browser automatically sends cookies (`credentials: 'include'` is set by `apiFetch`), and the Django backend authenticates via the access_token cookie.
- **Error handling**: API errors show a toast. Rating fetch failure (in server load) is silent — user just sees no personal rating.


Changes from Phase 2d +page.svelte:
| Area | Before | After |
|------|--------|-------|
| Script imports | 4 component imports | + `RatingStars`, `upsertRating`, `deleteRatingById`, `toast`, `$app/stores` |
| State | none (stateless) | `userRating`, `ratingId`, `saving`, `handleRate` |
| Cover section (desktop) | Text `{avg_rating.toFixed(1)} avg rating` | `avg_rating.toFixed(2)` + ratings count |
| Cover section (mobile) | Text `{avg_rating.toFixed(1)} avg rating` | `avg_rating.toFixed(2)` + compact count |
| Content column | `BookHeader` → `BookMeta` → `BookDescription` | `BookHeader` → **user rating widget** → `BookMeta` → `BookDescription` |

- [ ] **Step 3: Run svelte-check**

```bash
cd svelte-frontend && npm run check 2>&1 | tail -20
```
Expected: zero errors for book route files. If `data.user` or `data.userRating` types aren't recognized, the SvelteKit generated `$types.d.ts` might need to be regenerated — run `npm run check` after a dev server start (`npm run dev` briefly) or run `npx svelte-kit sync`.

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/src/routes/books/\[slug\]/+page.svelte
git commit -m "feat(books): add RatingStars widget to book detail page"
```

---

## Task 5: Verify — type check, lint, final commit

- [ ] **Step 1: Run full svelte-check**

```bash
cd svelte-frontend && npm run check 2>&1
```
Expected: zero errors. If errors exist, list them and fix before proceeding.

- [ ] **Step 2: Run ESLint**

```bash
cd svelte-frontend && npm run lint 2>&1
```
Expected: zero errors. Run `npm run lint -- --fix` if auto-fixable.

- [ ] **Step 3: Verify all expected files exist**

```bash
test -f svelte-frontend/src/lib/api/ratings.ts && echo "OK" || echo "MISSING: ratings.ts"
test -f svelte-frontend/src/routes/books/\[slug\]/+page.server.ts && echo "OK" || echo "MISSING: +page.server.ts"
test -f svelte-frontend/src/routes/books/\[slug\]/+page.svelte && echo "OK" || echo "MISSING: +page.svelte"
```
Expected: three `OK`

- [ ] **Step 4: Verify clean git status**

```bash
git status
```
Expected: working tree clean or only unrelated changes.

- [ ] **Step 5: Final commit (if any lint fixes)**

```bash
# If lint had auto-fixable issues:
git add -A && git commit -m "chore(lint): auto-fixes for Phase 3e files"

# Otherwise confirm clean:
git status
```

---

## Self-Review Checklist

### 1. Spec coverage

| Spec requirement | Covered by |
|---|---|
| RatingWidget obok BookHero | Task 4: user rating widget between BookHeader and BookMeta |
| Niezalogowany: tylko średnia + liczba | Task 4: community avg as text `{avg_rating.toFixed(2)} ({ratings_count} ratings)`, user widget hidden (`#if data.user`) |
| Zalogowany: własna ocena + interaktywne gwiazdki | Task 2: `fetchUserRating` in server load; Task 4: `#if data.user` renders `RatingStars` with `onRate` |
| Kliknięcie gwiazdki → PUT /api/ratings/ | Task 4: `handleRate` calls `upsertRating(fetch, slug, star)` → PUT |
| Kliknięcie tej samej gwiazdki → DELETE /api/ratings/{id}/ | Task 4: `star === userRating` (page handler toggle) → `deleteRatingById(fetch, ratingId)` → DELETE |
| Loading ratingu → skeleton | SSR resolves before render, no skeleton needed for initial load. During mutation: `saving` state → opacity-50 |
| Error fetch → ciche, pokaż tylko średnią | Task 2: non-fatal `fetchUserRating` error → `userRating = null` |
| Error mutate → toast | Task 4: `toast.error('Failed to save rating. Try again.')` |
| Reużycie RatingStars z 3c | Task 4: imports `RatingStars` — shared component, same contract as 3c |
| Średnia społeczności jako tekst obok interaktywnych gwiazd | Task 4: text `{avg_rating.toFixed(2)} ({ratings_count} ratings)` |
| GET /api/ratings/?book_slug=X | Task 1: `fetchUserRating(fetchFn, bookSlug)` → `GET /ratings/?book_slug=...` |
| PUT /api/ratings/ z body | Task 1: `upsertRating(fetchFn, bookSlug, rating)` → `PUT /ratings/ { book_slug, rating }` |
| DELETE /api/ratings/{id}/ | Task 1: `deleteRatingById(fetchFn, ratingId)` → `DELETE /ratings/{id}/` (added by 3c) |
| User z +page.server.ts | Task 2: `const { user } = await parent()` |
| Równoległe fetchowanie książki i ratingu | Task 2: `Promise.all([getBook, fetchUserRating])` |

### 2. States coverage

| State | Handling |
|---|---|
| Niezalogowany | `data.user` falsy → `#if data.user` hides widget; community avg text visible |
| Zalogowany, brak oceny | `userRating = null` → RatingStars shows empty stars + "Rate this book" |
| Zalogowany, oceniono | `userRating = 4` → RatingStars shows 4 filled stars + "Your rating: 4" |
| Loading ratingu (SSR) | SSR resolves fully before render — no skeleton needed |
| Error fetch ratingu | Non-fatal in server load → `userRating = null`, page renders without user rating |
| Saving (mutation in progress) | `saving = true` → container opacity-50, RatingStars disabled via `loading` prop internally |
| Mutation success (PUT) | `userRating = result.rating`, `ratingId = result.id` |
| Mutation success (DELETE) | `userRating = null`, `ratingId = null` |
| Mutation error | `toast.error('Failed to save rating. Try again.')` — console: error details |

### 3. Type consistency

- `RatingResponse` interface matches DRF response: `{ id: number, book_slug: string, rating: number }` (defined in `ratings.ts` by 3c)
- `fetchUserRating` returns `{ data: RatingResponse | null, error: ApiError | null }` — matches `apiFetch` pattern
- `upsertRating` and `deleteRatingById` use same return type pattern
- `PageData` auto-generated by SvelteKit from `+page.server.ts` return type
- `data.user` typed as `UserMe | null` (from root layout)
- `data.userRating` typed as `{ rating: number, id: number } | null`
- `data.book` typed as `Book` (unchanged from Phase 2d)

### 4. Component API consistency

- `RatingStars` props: `rating` (number|null), `onRate` (async callback, receives 1-5), `readonly` (bool), `size` (sm/md). Toggle logic lives in the page handler, not in the component.
- `BookCover` — unchanged
- `BookHeader` — unchanged
- `BookMeta` — unchanged
- `BookDescription` — unchanged

### 5. Error mapping

| Scenario | What happens |
|---|---|
| API returns 200 + rating list | `fetchUserRating` returns first element → `userRating` populated |
| API returns 200 + empty list | `fetchUserRating` returns null → `userRating = null` |
| API returns 401 (unauthenticated but SSR has cookie) | `apiFetch` retries refresh → if still 401, returns error → non-fatal |
| API returns 500 on rating fetch | Non-fatal → page renders without user rating |
| PUT returns 201/200 | `upsertRating` returns `Rating` → update state |
| PUT returns 400 (invalid rating) | `upsertRating` returns error → toast |
| DELETE returns 204 | `deleteRatingById` returns null data, no error → clear state |
| DELETE returns 404 | `deleteRatingById` returns error → toast |
| Network error (browser offline) | `apiFetch` catches → `{ status: 0, detail: String(err) }` → toast |
| Book page itself 404 | `getBook` returns 404 → `throw error(404)` → `+error.svelte` renders "Book not found" |

### 6. Non-functional checks

- [ ] No localStorage, sessionStorage — state is in SvelteKit SSR (server load) + reactive Svelte 5 `$state`
- [ ] No polling or subscriptions — rating fetched once on page load
- [ ] No optimistic updates — state updates only after API success
- [ ] Community average never writes to server — displayed as text, no interactive component
- [ ] Mutations use `credentials: 'include'` — handled by `apiFetch` which sets it

### 7. Placeholder scan

No TBD, TODO, FIXME, "implement later", or vague patterns. Every step has exact code, exact commands, exact expected output.

---

## Execution Handoff

Plan complete. **5 tasks, ~5 commits.** Each task produces a working, committable state.

**Dependencies:**
- Must have M2 Phase 2d complete (book detail route exists)
- Must have M3 Phase 3a complete (Rating API responds)
- RatingStars component may need enhancement (Task 3 handles this if 3c didn't)

**Execution order:** Sequential (each task builds on the previous). Tasks 2 and 3 can be swapped if desired.

Two execution approaches:
1. **Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks
2. **Inline Execution** — execute tasks in this session using `/executing-plans`
