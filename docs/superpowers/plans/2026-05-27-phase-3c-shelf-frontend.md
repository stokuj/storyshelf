# Phase 3c: /shelf Frontend — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Shelf page with 3 tabs (Want to Read / Reading / Read), inline actions (status change, rating, progress bar).

**Architecture:** Single `/shelf` route with auth guard. `+page.ts` fetches all entries + ratings via API, merging rating IDs locally. Client-side tabs filter with `$derived`. Components: `ShelfBookCard` composing `RatingStars` (existing, extended), `StatusDropdown`, `ProgressBar`. Optimistic updates on mutations with rollback on error.

**Tech Stack:** SvelteKit 2, Svelte 5 runes (`$state`, `$derived`, `$props`, `$effect`), Tailwind v4, TypeScript.

**Files to create/modify:**
```
svelte-frontend/src/
├── lib/
│   ├── api/
│   │   ├── shelf.ts                    NEW — shelf API client
│   │   └── ratings.ts                  NEW — ratings API client (shared with 3e)
│   └── components/
│       ├── book/RatingStars.svelte     MODIFY — add async onRate callback + loading state
│       └── shelf/
│           ├── ProgressBar.svelte      NEW
│           ├── StatusDropdown.svelte   NEW
│           └── ShelfBookCard.svelte    NEW
└── routes/shelf/
    ├── +layout.server.ts              NEW — auth guard
    ├── +page.ts                       NEW — load shelf entries + ratings
    └── +page.svelte                   NEW — tabs, cards, optimistic mutations
```

---

## Task 1: API client — `lib/api/shelf.ts`

- [ ] Create `svelte-frontend/src/lib/api/shelf.ts`

**File: `svelte-frontend/src/lib/api/shelf.ts`**
```typescript
import { apiFetch, type ApiError } from './_client';

// ---- Types (matching backend 3b response) ----

export interface ShelfEntryBook {
	slug: string;
	title: string;
	cover_url: string | null;
	authors: { name: string }[];
	genres: { name: string }[];
	avg_rating: number;
	page_count: number | null;
}

export interface ShelfEntry {
	id: number;
	book_slug: string;
	status: 'WANT_TO_READ' | 'READING' | 'READ';
	start_date: string | null;
	finish_date: string | null;
	current_page: number | null;
	user_rating: number | null;
	book: ShelfEntryBook;
}

export interface ShelfEntryUpdate {
	status?: string;
	start_date?: string | null;
	finish_date?: string | null;
	current_page?: number | null;
}

// ---- Shelf Entry API ----

/**
 * Fetch all shelf entries for the authenticated user.
 * Pass SvelteKit's `fetch` in load functions, or global `fetch` client-side.
 */
export async function fetchShelfEntries(fetchFn: typeof fetch) {
	return apiFetch<ShelfEntry[]>(fetchFn, '/shelf/entries/');
}

/**
 * Update a shelf entry (status, dates, current_page).
 * Uses PATCH — only send fields that changed.
 * Accepts fetchFn for SSR compatibility; use global `fetch` in client-side handlers.
 */
export async function updateShelfEntry(fetchFn: typeof fetch, id: number, data: ShelfEntryUpdate) {
	return apiFetch<ShelfEntry>(fetchFn, `/shelf/entries/${id}/`, {
		method: 'PATCH',
		body: JSON.stringify(data)
	});
}

/**
 * Delete a shelf entry entirely (remove book from all shelves).
 * Accepts fetchFn for SSR compatibility; use global `fetch` in client-side handlers.
 */
export async function deleteShelfEntry(fetchFn: typeof fetch, id: number) {
	return apiFetch<null>(fetchFn, `/shelf/entries/${id}/`, { method: 'DELETE' });
}
```

- [ ] `git add svelte-frontend/src/lib/api/shelf.ts`
- [ ] `git commit -m "feat(shelf): add shelf API client"`

### Ratings API client — `lib/api/ratings.ts`

- [ ] Create `svelte-frontend/src/lib/api/ratings.ts`

**File: `svelte-frontend/src/lib/api/ratings.ts`**
```typescript
import { apiFetch, type ApiError } from './_client';

export interface RatingResponse {
	id: number;
	book_slug: string;
	rating: number;
}

/**
 * Fetch all ratings for the authenticated user.
 * Used on shelf page load to get rating IDs for deletion.
 */
export async function fetchRatings(fetchFn: typeof fetch) {
	return apiFetch<RatingResponse[]>(fetchFn, '/ratings/');
}

/**
 * Upsert a rating (PUT). Returns the rating object including its id.
 * If a rating for this user+book already exists, it's updated.
 * Supports both server-side and client-side via fetchFn parameter.
 */
export async function upsertRating(fetchFn: typeof fetch, bookSlug: string, rating: number) {
	return apiFetch<RatingResponse>(fetchFn, '/ratings/', {
		method: 'PUT',
		body: JSON.stringify({ book_slug: bookSlug, rating })
	});
}

/**
 * Delete a rating by its ID.
 */
export async function deleteRatingById(fetchFn: typeof fetch, id: number) {
	return apiFetch<null>(fetchFn, `/ratings/${id}/`, { method: 'DELETE' });
}
```

- [ ] `git add svelte-frontend/src/lib/api/ratings.ts`
- [ ] `git commit -m "feat(api): add ratings API client — fetchRatings, upsertRating, deleteRatingById"`

---

## Task 2: RatingStars — interactive mode (modify existing)

- [ ] Read `svelte-frontend/src/lib/components/book/RatingStars.svelte` (exists, unused)
- [ ] Modify to support async `onRate` callback + loading state while preserving display-only mode

**File: `svelte-frontend/src/lib/components/book/RatingStars.svelte`**
```svelte
<script lang="ts">
	import { Star } from 'lucide-svelte';

	interface Props {
		/** Current rating value (null = unrated). For interactive mode, this is the display-only prop — parent updates it after onRate resolves. */
		rating?: number | null;
		/** Optional async callback. When provided, clicking a star calls this and disables interaction during the promise. */
		onRate?: (rating: number) => Promise<void>;
		/** Disable all interaction (display-only) */
		readonly?: boolean;
		/** Star size */
		size?: 'sm' | 'md';
	}

	let { rating = null, onRate = undefined, readonly = false, size = 'md' }: Props = $props();

	const sizeMap: Record<string, string> = { sm: 'size-3', md: 'size-4' };
	const sizeCls = $derived(sizeMap[size] ?? 'size-4');

	let hoverValue = $state(0);
	let loading = $state(false);
	let errorMessage = $state('');

	/** Display value: 0 = no star filled, 1-5 = filled up to that star */
	const displayValue = $derived(hoverValue > 0 ? hoverValue : (rating ?? 0));

	async function handleClick(star: number) {
		if (readonly || loading) return;
		if (!onRate) return;

		errorMessage = '';
		loading = true;
		try {
			await onRate(star);
		} catch (err) {
			errorMessage = String(err);
		} finally {
			loading = false;
		}
	}
</script>

<div class="inline-flex flex-col">
	<div class="inline-flex items-center gap-0.5">
		{#each [1, 2, 3, 4, 5] as star (star)}
			<button
				type="button"
				class="transition-colors {readonly || loading || !onRate
					? 'cursor-default'
					: 'cursor-pointer hover:scale-110 transition-transform'}"
				class:text-accent={star <= displayValue}
				class:text-rule={star > displayValue}
				disabled={readonly || loading}
				aria-label="{star} star{star > 1 ? 's' : ''}"
				onclick={() => handleClick(star)}
				onmouseenter={() => {
					if (!readonly && !loading && onRate) hoverValue = star;
				}}
				onmouseleave={() => {
					hoverValue = 0;
				}}
			>
				<Star
					class={sizeCls}
					fill={star <= displayValue ? 'currentColor' : 'none'}
				/>
			</button>
		{/each}
	</div>
	{#if errorMessage}
		<p class="text-xs text-danger mt-1">{errorMessage}</p>
	{/if}
</div>
```

- [ ] Verify: `grep -r "RatingStars" svelte-frontend/src/` shows no imports (only self) — safe to change props
- [ ] `git add svelte-frontend/src/lib/components/book/RatingStars.svelte`
- [ ] `git commit -m "feat(ui): add async onRate callback + loading state to RatingStars"`

---

## Task 3: ProgressBar — `lib/components/shelf/ProgressBar.svelte`

- [ ] Create directory: `mkdir -p svelte-frontend/src/lib/components/shelf`
- [ ] Create component

**File: `svelte-frontend/src/lib/components/shelf/ProgressBar.svelte`**
```svelte
<script lang="ts">
	interface Props {
		/** Current page number (null if not set) */
		current: number | null;
		/** Total pages in the book (null if unknown) */
		total: number | null;
	}

	let { current, total }: Props = $props();

	const percent = $derived(
		current != null && total != null && total > 0
			? Math.round((current / total) * 100)
			: null
	);

	const label = $derived(() => {
		const curPart = current != null ? String(current) : '?';
		const totPart = total != null ? String(total) : '?';
		return `${curPart} / ${totPart} pages`;
	});
</script>

{#if current != null}
	<div class="w-full space-y-1">
		<div class="w-full bg-rule rounded-full h-1.5 overflow-hidden">
			<div
				class="bg-accent h-1.5 rounded-full transition-all duration-300"
				style="width:{percent != null ? percent : 0}%"
			></div>
		</div>
		<div class="flex items-center justify-between">
			<span class="text-xs text-muted">{label()}</span>
			{#if percent != null}
				<span class="text-xs text-muted">{percent}%</span>
			{/if}
		</div>
	</div>
{/if}
```

- [ ] `git add svelte-frontend/src/lib/components/shelf/ProgressBar.svelte`
- [ ] `git commit -m "feat(ui): add ProgressBar component"`

---

## Task 4: StatusDropdown — `lib/components/shelf/StatusDropdown.svelte`

- [ ] Create component

**File: `svelte-frontend/src/lib/components/shelf/StatusDropdown.svelte`**
```svelte
<script lang="ts">
	import { ChevronDown } from 'lucide-svelte';

	interface Props {
		/** Current shelf status */
		currentStatus: string;
		/** Callback when user selects a new status. Returns void or Promise. */
		onChange: (status: string) => Promise<void> | void;
		/** Disable while mutation is in flight */
		disabled?: boolean;
	}

	let { currentStatus, onChange, disabled = false }: Props = $props();

	const options: { value: string; label: string; color: string }[] = [
		{ value: 'WANT_TO_READ', label: 'Want to Read', color: 'text-info border-info/30 bg-info/5' },
		{ value: 'READING', label: 'Reading', color: 'text-warning border-warning/30 bg-warning/5' },
		{ value: 'READ', label: 'Read', color: 'text-success border-success/30 bg-success/5' }
	];

	let open = $state(false);
	let loading = $state(false);

	const currentOption = $derived(options.find((o) => o.value === currentStatus));

	async function selectStatus(value: string) {
		if (disabled || loading || value === currentStatus) return;
		open = false;
		loading = true;
		try {
			await onChange(value);
		} finally {
			loading = false;
		}
	}

	function toggleOpen() {
		if (disabled || loading) return;
		open = !open;
	}

	function closeDropdown() {
		open = false;
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') closeDropdown();
	}
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="relative" onkeydown={handleKeydown}>
	<button
		type="button"
		class="flex items-center justify-between gap-1.5 w-full rounded-md border border-rule bg-surface px-2.5 py-1.5 text-xs font-medium transition-colors hover:bg-paper-2 disabled:opacity-50 disabled:cursor-not-allowed {currentOption?.color ?? ''}"
		disabled={disabled || loading}
		onclick={toggleOpen}
		aria-expanded={open}
		aria-haspopup="listbox"
	>
		<span>{currentOption?.label ?? currentStatus}</span>
		<ChevronDown class="size-3 text-muted {open ? 'rotate-180' : ''} transition-transform" />
	</button>

	{#if open}
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div
			class="absolute top-full left-0 right-0 mt-1 z-10 rounded-md border border-rule bg-surface shadow-lg py-1"
			role="listbox"
		>
			{#each options as opt (opt.value)}
				<button
					type="button"
					class="w-full text-left px-2.5 py-1.5 text-xs font-medium transition-colors hover:bg-paper-2 {opt.value === currentStatus ? 'font-semibold' : ''} {opt.color}"
					role="option"
					aria-selected={opt.value === currentStatus}
					onclick={() => selectStatus(opt.value)}
				>
					{opt.label}
				</button>
			{/each}
		</div>
	{/if}

	<!-- Backdrop to close on outside click -->
	{#if open}
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<button class="fixed inset-0 z-0" onclick={closeDropdown} tabindex="-1"></button>
	{/if}
</div>
```

- [ ] `git add svelte-frontend/src/lib/components/shelf/StatusDropdown.svelte`
- [ ] `git commit -m "feat(ui): add StatusDropdown component"`

---

## Task 5: ShelfBookCard — `lib/components/shelf/ShelfBookCard.svelte`

- [ ] Create component

**File: `svelte-frontend/src/lib/components/shelf/ShelfBookCard.svelte`**
```svelte
<script lang="ts">
	import { goto } from '$app/navigation';
	import { BookOpen, Trash2 } from 'lucide-svelte';
	import BookCover from '$lib/components/book/BookCover.svelte';
	import RatingStars from '$lib/components/book/RatingStars.svelte';
	import ProgressBar from './ProgressBar.svelte';
	import StatusDropdown from './StatusDropdown.svelte';
	import { Badge } from '$lib/components/ui/badge';
	import type { ShelfEntry } from '$lib/api/shelf';

	interface Props {
		entry: ShelfEntry;
		/** Called with the updated entry after any mutation succeeds */
		onUpdate: (updated: ShelfEntry) => void;
		/** Called when entry should be removed from list */
		onDelete: (id: number) => void;
		/** Called when user wants to rate: (bookSlug, newRating) */
		onRate: (bookSlug: string, rating: number, entryId: number) => Promise<void>;
		/** Called when user changes status: (entryId, newStatus) */
		onStatusChange: (entryId: number, status: string) => Promise<void>;
	}

	let { entry, onUpdate, onDelete, onRate, onStatusChange }: Props = $props();

	const book = $derived(entry.book);
	const authors = $derived(book.authors.map((a) => a.name).join(', '));

	const statusColors: Record<string, string> = {
		WANT_TO_READ: 'border-info/30 text-info',
		READING: 'border-warning/30 text-warning',
		READ: 'border-success/30 text-success'
	};

	const statusLabels: Record<string, string> = {
		WANT_TO_READ: 'Want to Read',
		READING: 'Reading',
		READ: 'Read'
	};

	let confirming = $state(false);

	async function handleRate(rating: number) {
		await onRate(entry.book_slug, rating, entry.id);
	}

	async function handleStatusChange(status: string) {
		await onStatusChange(entry.id, status);
	}

	function handleDelete() {
		confirming = true;
	}

	function confirmDelete() {
		confirming = false;
		onDelete(entry.id);
	}

	function cancelDelete() {
		confirming = false;
	}

	function navigateToBook() {
		goto(`/books/${book.slug}`);
	}
</script>

<div class="flex gap-4 rounded-lg border border-rule bg-surface p-4 shadow-sm hover:shadow-md transition-shadow">
	<!-- Cover (clickable) -->
	<button type="button" class="flex-shrink-0 cursor-pointer" onclick={navigateToBook} aria-label="Go to book detail">
		<BookCover coverUrl={book.cover_url} title={book.title} size="sm" />
	</button>

	<!-- Content -->
	<div class="flex-1 min-w-0 space-y-2">
		<!-- Title + author + status badge -->
		<div class="space-y-0.5">
			<button type="button" class="text-left cursor-pointer hover:text-accent transition-colors" onclick={navigateToBook}>
				<h3 class="font-sans text-sm font-semibold text-ink line-clamp-1">{book.title}</h3>
			</button>
			<p class="text-xs text-muted">{authors}</p>
			<div class="flex flex-wrap items-center gap-2 pt-0.5">
				<Badge variant="outline" class="text-[10px] px-1.5 py-0 {statusColors[entry.status] ?? ''}">
					{statusLabels[entry.status] ?? entry.status}
				</Badge>
				{#if book.avg_rating > 0}
					<span class="text-[10px] text-muted">★ {book.avg_rating.toFixed(1)}</span>
				{/if}
			</div>
		</div>

		<!-- Rating stars (interactive) -->
		<div class="pt-1">
			<RatingStars rating={entry.user_rating} onRate={handleRate} size="sm" />
		</div>

		<!-- Progress bar (only when READING and current_page is set) -->
		{#if entry.status === 'READING'}
			<ProgressBar current={entry.current_page} total={book.page_count} />
		{/if}

		<!-- Actions row -->
		<div class="flex items-center justify-between gap-2 pt-1">
			<div class="w-36">
				<StatusDropdown
					currentStatus={entry.status}
					onChange={handleStatusChange}
				/>
			</div>
			{#if confirming}
				<div class="flex items-center gap-1">
					<button
						type="button"
						class="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-danger bg-danger/10 hover:bg-danger/20 transition-colors"
						onclick={confirmDelete}
						aria-label="Confirm remove from shelf"
					>
						<Trash2 class="size-3" />
						<span>Confirm remove?</span>
					</button>
					<button
						type="button"
						class="rounded-md px-2 py-1 text-xs text-muted hover:text-ink transition-colors"
						onclick={cancelDelete}
						aria-label="Cancel remove"
					>
						Cancel
					</button>
				</div>
			{:else}
				<button
					type="button"
					class="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted hover:text-danger hover:bg-danger/5 transition-colors"
					onclick={handleDelete}
					aria-label="Remove from shelf"
				>
					<Trash2 class="size-3" />
					<span>Remove</span>
				</button>
			{/if}
		</div>
	</div>
</div>
```

- [ ] `git add svelte-frontend/src/lib/components/shelf/ShelfBookCard.svelte`
- [ ] `git commit -m "feat(ui): add ShelfBookCard component"`

---

## Task 6: Auth guard — `routes/shelf/+layout.server.ts`

- [ ] Create directory: `mkdir -p svelte-frontend/src/routes/shelf`
- [ ] Create file matching the exact pattern from `settings/+layout.server.ts`

**File: `svelte-frontend/src/routes/shelf/+layout.server.ts`**
```typescript
import { redirectIfNotLoggedIn } from '$lib/server/auth';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ parent, url }) => {
	const { user } = await parent();
	redirectIfNotLoggedIn(user, url);
	return { user };
};
```

- [ ] `git add svelte-frontend/src/routes/shelf/+layout.server.ts`
- [ ] `git commit -m "feat(shelf): add auth guard for /shelf route"`

---

## Task 7: Page loader — `routes/shelf/+page.ts`

- [ ] Create universal load function. Fetches shelf entries + ratings, merges rating IDs.

**File: `svelte-frontend/src/routes/shelf/+page.ts`**
```typescript
import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';
import { fetchShelfEntries } from '$lib/api/shelf';
import { fetchRatings } from '$lib/api/ratings';
import type { ShelfEntry } from '$lib/api/shelf';
import type { RatingResponse } from '$lib/api/ratings';

/** Internal type: ShelfEntry augmented with rating_id for delete operations */
export interface ShelfEntryWithRating extends ShelfEntry {
	rating_id: number | null;
}

export const load: PageLoad = async ({ fetch }) => {
	const [entriesResult, ratingsResult] = await Promise.all([
		fetchShelfEntries(fetch),
		fetchRatings(fetch)
	]);

	if (entriesResult.error) {
		throw error(
			entriesResult.error.status || 500,
			entriesResult.error.detail || 'Failed to load shelf entries'
		);
	}

	// Build a book_slug → rating_id map for merging
	const ratingByBookSlug = new Map<string, number>();
	if (ratingsResult.data) {
		for (const r of ratingsResult.data) {
			ratingByBookSlug.set(r.book_slug, r.id);
		}
	}

	// Augment each entry with its rating_id (for deletion)
	const entries: ShelfEntryWithRating[] = (entriesResult.data || []).map((entry) => ({
		...entry,
		rating_id: ratingByBookSlug.get(entry.book_slug) ?? null
	}));

	return { entries };
};
```

- [ ] `git add svelte-frontend/src/routes/shelf/+page.ts`
- [ ] `git commit -m "feat(shelf): add page loader with entries + ratings merge"`

---

## Task 8: Page component — `routes/shelf/+page.svelte`

- [ ] Create full page with tabs, cards, optimistic updates, loading/error/empty states

**File: `svelte-frontend/src/routes/shelf/+page.svelte`**
```svelte
<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { BookOpen, Library, BookMarked, AlertCircle, Loader2 } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import ShelfBookCard from '$lib/components/shelf/ShelfBookCard.svelte';
	import { upsertRating, deleteRatingById } from '$lib/api/ratings';
	import {
		updateShelfEntry,
		deleteShelfEntry,
		type ShelfEntry,
		type ShelfEntryUpdate
	} from '$lib/api/shelf';
	import type { ShelfEntryWithRating } from './$page.ts';

	interface Props {
		data: {
			entries: ShelfEntryWithRating[];
		};
	}

	let { data }: Props = $props();

	// ---- Reactive state ----
	let entries = $state(data.entries);
	let activeTab = $state<'WANT_TO_READ' | 'READING' | 'READ'>('WANT_TO_READ');
	let loadingStates = $state<Record<string, boolean>>({});

	// ---- Tab definitions ----
	type TabId = 'WANT_TO_READ' | 'READING' | 'READ';
	const tabs: { id: TabId; label: string; icon: typeof BookOpen }[] = [
		{ id: 'WANT_TO_READ', label: 'Want to Read', icon: BookOpen },
		{ id: 'READING', label: 'Reading', icon: Library },
		{ id: 'READ', label: 'Read', icon: BookMarked }
	];

	const emptyMessages: Record<TabId, { title: string; description: string; cta?: { label: string; href: string } }> = {
		WANT_TO_READ: {
			title: 'No books waiting',
			description: 'Books you want to read will appear here.',
			cta: { label: 'Discover books', href: '/discover' }
		},
		READING: {
			title: 'Not reading anything right now',
			description: 'Books you are currently reading will appear here.'
		},
		READ: {
			title: 'No finished books yet',
			description: 'Books you have finished reading will appear here.'
		}
	};

	// ---- Derive filtered arrays ----
	const filtered = $derived(
		entries.filter((e) => e.status === activeTab)
	);

	const tabCounts = $derived({
		WANT_TO_READ: entries.filter((e) => e.status === 'WANT_TO_READ').length,
		READING: entries.filter((e) => e.status === 'READING').length,
		READ: entries.filter((e) => e.status === 'READ').length
	});

	// ---- Sync tab from ?tab= query param on mount ----
	$effect(() => {
		const param = $page.url.searchParams.get('tab');
		if (param === 'reading') activeTab = 'READING';
		else if (param === 'read') activeTab = 'READ';
		else if (param === 'want-to-read') activeTab = 'WANT_TO_READ';
	});

	// ---- Mutations ----

	async function handleStatusChange(entryId: number, newStatus: string) {
		const index = entries.findIndex((e) => e.id === entryId);
		if (index === -1) return;

		const oldStatus = entries[index].status;
		const oldFinishDate = entries[index].finish_date;

		// Optimistic update
		const updates: Partial<ShelfEntryWithRating> = { status: newStatus as ShelfEntry['status'] };
		if (newStatus === 'READ' && !entries[index].finish_date) {
			updates.finish_date = new Date().toISOString().split('T')[0];
		}
		entries[index] = { ...entries[index], ...updates };

		const payload: ShelfEntryUpdate = { status: newStatus };
		if (updates.finish_date) payload.finish_date = updates.finish_date;

		const { error } = await updateShelfEntry(fetch, entryId, payload);
		if (error) {
			// Rollback
			entries[index] = { ...entries[index], status: oldStatus, finish_date: oldFinishDate };
			console.error('Failed to update status:', error.detail);
		}
	}

	async function handleRate(bookSlug: string, rating: number, entryId: number) {
		const index = entries.findIndex((e) => e.id === entryId);
		if (index === -1) return;

		const entry = entries[index];
		const oldRating = entry.user_rating;
		const oldRatingId = entry.rating_id;

		// If clicking the same star that's already rated → delete
		if (rating === oldRating && oldRatingId != null) {
			// Optimistic: clear rating
			entries[index] = { ...entry, user_rating: null, rating_id: null };

			const { error } = await deleteRatingById(fetch, oldRatingId);
			if (error) {
				entries[index] = { ...entry, user_rating: oldRating, rating_id: oldRatingId };
				console.error('Failed to delete rating:', error.detail);
			}
			return;
		}

		// Upsert: set new rating
		entries[index] = { ...entry, user_rating: rating };

		const { data: ratingData, error } = await upsertRating(fetch, bookSlug, rating);
		if (error || !ratingData) {
			entries[index] = { ...entry, user_rating: oldRating, rating_id: oldRatingId };
			console.error('Failed to upsert rating:', error?.detail);
		} else {
			// Store rating_id for future deletes
			entries[index] = { ...entries[index], rating_id: ratingData.id, user_rating: ratingData.rating };
		}
	}

	async function handleDelete(entryId: number) {
		const index = entries.findIndex((e) => e.id === entryId);
		if (index === -1) return;

		const removed = entries[index];

		// Optimistic remove
		entries = entries.filter((e) => e.id !== entryId);

		const { error } = await deleteShelfEntry(fetch, entryId);
		if (error) {
			// Rollback: reinsert
			entries = [removed, ...entries];
			console.error('Failed to delete entry:', error.detail);
		}
	}

	function setActiveTab(tabId: TabId) {
		activeTab = tabId;
		// Update URL without navigation
		const url = new URL($page.url);
		const paramMap: Record<TabId, string> = {
			WANT_TO_READ: 'want-to-read',
			READING: 'reading',
			READ: 'read'
		};
		url.searchParams.set('tab', paramMap[tabId]);
		goto(url, { replaceState: true, noScroll: true, keepFocus: true });
	}
</script>

<svelte:head>
	<title>My Shelf — Storyshelf</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div>
		<h1 class="font-display text-3xl tracking-tight font-medium text-ink">My Shelf</h1>
		<p class="text-sm text-muted mt-1">Track what you read and want to read.</p>
	</div>

	<!-- Tabs bar -->
	<nav class="flex border-b border-rule" role="tablist">
		{#each tabs as tab (tab.id)}
			<button
				type="button"
				role="tab"
				class="flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors {activeTab === tab.id
					? 'border-accent text-accent'
					: 'border-transparent text-muted hover:text-ink hover:border-rule'}"
				aria-selected={activeTab === tab.id}
				onclick={() => setActiveTab(tab.id)}
			>
				<tab.icon class="size-4" />
				<span>{tab.label}</span>
				<span class="ml-1 rounded-full bg-paper-2 px-1.5 py-0.5 text-[10px] font-medium text-muted leading-none">
					{tabCounts[tab.id]}
				</span>
			</button>
		{/each}
	</nav>

	<!-- Tab content -->
	{#if filtered.length > 0}
		<div class="space-y-3">
			{#each filtered as entry (entry.id)}
				<ShelfBookCard
					{entry}
					onUpdate={(updated) => {
						const idx = entries.findIndex((e) => e.id === updated.id);
						if (idx !== -1) entries[idx] = { ...entries[idx], ...updated };
					}}
					onDelete={handleDelete}
					onRate={handleRate}
					onStatusChange={handleStatusChange}
				/>
			{/each}
		</div>
	{:else}
		{@const msg = emptyMessages[activeTab]}
		<EmptyState
			icon={tabs.find((t) => t.id === activeTab)?.icon ?? BookOpen}
			title={msg.title}
			description={msg.description}
			cta={msg.cta}
		/>
	{/if}
</div>
```

- [ ] `git add svelte-frontend/src/routes/shelf/+page.svelte`
- [ ] `git commit -m "feat(shelf): add /shelf page with tabs and optimistic mutations"`

---

## Task 9: Generate API types

- [ ] Run `npm run types:api` (from `svelte-frontend/`)
- [ ] Verify `src/lib/types/api.generated.ts` was updated
- [ ] `git add svelte-frontend/src/lib/types/api.generated.ts`
- [ ] `git commit -m "chore(types): regenerate API types after shelf endpoints"`

---

## Task 10: Verify

- [ ] Run `npm run check` from `svelte-frontend/` — must have **0 errors**
- [ ] Run `npm run lint` from `svelte-frontend/` — must have **0 errors**
- [ ] If any errors, fix them and re-commit
- [ ] Run `npm run build` to verify production build
- [ ] `git add` any remaining changes
- [ ] `git commit -m "chore(shelf): fix type/lint issues after shelf implementation"`

### Common issues to watch for

| Issue | Fix |
|-------|-----|
| `$lib/api/shelf.ts` uses `apiFetch` without `fetch` argument in client functions | `fetch` is global in browser — pass `fetch` (no `this`) |
| `$page.url` accessed in `+page.ts` (universal) | Use `$page` store in `.svelte`, not in `.ts` loader |
| `RouteParams` missing | Run `npm run types:api` or just use `any` in load params |
| `ReferenceError: fetch is not defined` in server-side code | All API client functions accept `fetchFn` parameter — pass SvelteKit's `fetch` in load functions; use global `fetch` in client-side event handlers |
| `ShelfEntryWithRating` type not exported | Exported from `+page.ts`, imported in `+page.svelte` |
| ESLint: `a11y_no_static_element_interactions` | Component files have `<!-- svelte-ignore -->` comments; page does not need them |

---

## Post-merge verification checklist

- [ ] `make dev-up` — Django + Svelte running
- [ ] Login → navigate to `/shelf` (not redirected)
- [ ] Tabs show correct empty states when no books on shelf
- [ ] Add books via Django admin → refresh → they appear in correct tabs
- [ ] Click status dropdown → changes to new status → card moves to correct tab
- [ ] Click rating stars → star fills → refresh keeps rating
- [ ] Click same star → rating removed
- [ ] Delete book → card removed
- [ ] `?tab=reading` URL sets correct active tab
- [ ] Logout → `/shelf` redirects to `/login`

---

> **Summary:** 9 new/modified files, 11 commits. No backend changes. Follows existing `apiFetch` return-value pattern, Svelte 5 `$props()`/`$state`/`$derived`/`$effect`, Template auth guard, and Tailwind v4 design tokens.
