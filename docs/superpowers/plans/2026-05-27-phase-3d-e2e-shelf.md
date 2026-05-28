# Phase 3d: Shelf E2E Tests — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 7 Playwright E2E tests covering shelf tabs, status changes, rating widget, progress bar, empty states, cross-user isolation, and delete.

**Architecture:** Single test file `e2e/shelf-status.spec.ts` + helper `e2e/helpers/seed.ts`. Seeds data via API helpers. Uses existing E2E infrastructure (login helpers, `baseUrl` from `fixtures.ts` etc.).

**Tech Stack:** Playwright, TypeScript.

**Prerequisites (must exist before these tests pass):**
- [ ] Django: `books/` app with at least one Book in DB (title="The Hobbit", slug="the-hobbit", page_count=423)
- [ ] Django: `shelf/` endpoints: `GET/POST /api/shelf/entries/`, `PATCH/DELETE /api/shelf/entries/{id}/` — fully tested in 3b
- [ ] Django: `ratings/` endpoint: `PUT /api/ratings/` — upsert, fully tested in 3a
- [ ] Frontend: `/shelf` route renders `ShelfBookCard`, `StatusDropdown`, `ProgressBar`, `RatingStars` with `data-testid` attributes (see below)

---

## Data-testid Convention (must be on components from Phase 3c)

| Element | Attribute | Notes |
|---|---|---|
| ShelfBookCard | `data-testid="shelf-book-card"` | Set on the card wrapper `<div>`. Include `data-status` and `data-book-slug` for filtering. |
| Tab button | `data-testid="shelf-tab"` | Each tab button. Include `data-tab` with value: `want_to_read`, `reading`, `read`. |
| Empty state | `data-testid="shelf-empty"` | Wrapper for empty-state message (visible when tab has zero entries). |
| ProgressBar | `data-testid="progress-bar"` | The bar wrapper. Visible only when `status=READING`. Include `data-current` and `data-total`. |
| RatingStars | `data-testid="rating-star"` | Each star `<button>`. Include `data-rating` (1-5). Stars with `data-selected="true"` when rating >= that value. |
| StatusDropdown | `data-testid="status-dropdown"` | The dropdown trigger button. Dropdown options identifiable by text ("Want to Read", "Reading", "Read"). |
| Delete button | `data-testid="shelf-delete-btn"` | Delete button/icon on card. |
| Delete confirm button | `data-testid="shelf-delete-confirm"` | Confirmation button shown after clicking delete, triggers actual DELETE API call. |

---

## File Layout

```
svelte-frontend/e2e/
├── shelf-status.spec.ts     NEW — 7 test cases
└── helpers/
    └── seed.ts              NEW — seedBooks(), seedShelfEntry(), cleanupShelfEntries()
```

---

## Task 1: Test file skeleton + seed helpers

**Create `svelte-frontend/e2e/helpers/seed.ts`** with functions to manage test data.

Complete code:

```typescript
// e2e/helpers/seed.ts
//
// Helper functions for seeding/cleaning test data for shelf E2E tests.
// Uses Playwright's APIRequestContext (authenticated via browser cookies).
//
// IMPORTANT: Books referenced by shelf entries must already exist in the dev DB.
// The dev setup (make dev-up) should include a seeding step. If books don't exist,
// tests will fail with 400 on POST /api/shelf/entries/.
//
// Ensure seed_books management command has been run before executing E2E tests.
// Add a pre-test assertion in the spec to verify books exist:
//   const res = await api.get('/api/books/?slug=the-hobbit');
//   expect(res.ok()).toBe(true);
//
// Known test books expected in the database:
//   slug="the-hobbit"            — page_count=423
//   slug="the-fellowship-of-the-ring"  — page_count=531
//   slug="the-two-towers"        — page_count=415

import { type APIRequestContext, type Cookie } from '@playwright/test';
import { API_BASE_URL } from '../fixtures';

export interface SeedShelfEntry {
	id: number;
	book_slug: string;
	status: string;
	current_page: number | null;
}

/**
 * Seed a single shelf entry via the authenticated API.
 * Creates a new APIRequestContext scoped to the user's cookies.
 */
export async function seedShelfEntry(
	entry: { book_slug: string; status: string; current_page?: number | null },
	cookies: Cookie[],
	playwright: typeof import('@playwright/test').playwright
): Promise<SeedShelfEntry> {
	const api = await playwright.request.newContext({
		baseURL: API_BASE_URL,
		storageState: { cookies }
	});

	const payload: Record<string, unknown> = {
		book_slug: entry.book_slug,
		status: entry.status
	};
	if (entry.current_page !== undefined && entry.current_page !== null) {
		payload.current_page = entry.current_page;
	}

	const res = await api.post('/api/shelf/entries/', { data: payload });
	if (!res.ok()) {
		const body = await res.text();
		await api.dispose();
		throw new Error(
			`[seed] Failed to create shelf entry: ${res.status()} ${body}. ` +
				`Payload: ${JSON.stringify(payload)}`
		);
	}

	const data = await res.json();
	await api.dispose();
	return { id: data.id, book_slug: data.book_slug, status: data.status, current_page: data.current_page };
}

/**
 * Delete all shelf entries for the current user via the authenticated API.
 * Gets the full list, then DELETE each one.
 */
export async function cleanupShelfEntries(
	cookies: Cookie[],
	playwright: typeof import('@playwright/test').playwright
): Promise<void> {
	const api = await playwright.request.newContext({
		baseURL: API_BASE_URL,
		storageState: { cookies }
	});

	// Get all entries for this user
	const listRes = await api.get('/api/shelf/entries/');
	if (!listRes.ok()) {
		console.warn(`[seed] cleanup: GET /api/shelf/entries/ returned ${listRes.status()}`);
		await api.dispose();
		return;
	}

	const entries: { id: number }[] = await listRes.json();
	for (const entry of entries) {
		const delRes = await api.delete(`/api/shelf/entries/${entry.id}/`);
		if (!delRes.ok()) {
			console.warn(`[seed] cleanup: DELETE entry ${entry.id} failed with ${delRes.status()}`);
		}
	}

	await api.dispose();
}
```

**Create `svelte-frontend/e2e/shelf-status.spec.ts`** — skeleton with imports, `describe`, helpers.

Complete code:

```typescript
// e2e/shelf-status.spec.ts
//
// E2E tests for /shelf — the user's reading shelf page.
// Requires: running Django backend + SvelteKit dev server.
// Run: npx playwright test e2e/shelf-status.spec.ts

import { test, expect, API_BASE_URL } from './fixtures';
import {
	seedShelfEntry,
	cleanupShelfEntries,
	type SeedShelfEntry
} from './helpers/seed';

// Test books that must exist in the dev database (seeded by make dev-up / management command).
const BOOKS = {
	H: { slug: 'the-hobbit', title: 'The Hobbit', page_count: 423 },
	F: { slug: 'the-fellowship-of-the-ring', title: 'The Fellowship of the Ring', page_count: 531 },
	T: { slug: 'the-two-towers', title: 'The Two Towers', page_count: 415 }
} as const;

test.describe('Shelf page', () => {
	/**
	 * beforeEach: ensure user is logged in, clean up any leftover data,
	 * seed entries needed for the test, then navigate to /shelf.
	 *
	 * Individual tests call a variant of this via helpers — NOT a shared
	 * test.beforeEach because each test seeds different data.
	 */

	// ── Helpers (within describe scope — get `authUser`, `page`, `playwright` via test args) ──

	async function setupShelf(
		page: import('@playwright/test').Page,
		playwright: typeof import('@playwright/test').playwright,
		entries: { book_slug: string; status: string; current_page?: number | null }[]
	): Promise<SeedShelfEntry[]> {
		const cookies = await page.context().cookies();
		const seeded: SeedShelfEntry[] = [];
		for (const e of entries) {
			const result = await seedShelfEntry(e, cookies, playwright);
			seeded.push(result);
		}
		await page.goto('/shelf');
		return seeded;
	}

	async function teardownShelf(
		page: import('@playwright/test').Page,
		playwright: typeof import('@playwright/test').playwright
	): Promise<void> {
		const cookies = await page.context().cookies();
		await cleanupShelfEntries(cookies, playwright);
	}

	// ── Utility: click a tab by data-testid ──

	async function clickTab(page: import('@playwright/test').Page, tab: 'want_to_read' | 'reading' | 'read') {
		await page.locator(`[data-testid="shelf-tab"][data-tab="${tab}"]`).click();
	}

	// ── Utility: count visible cards ──

	async function cardCount(page: import('@playwright/test').Page): Promise<number> {
		return page.locator('[data-testid="shelf-book-card"]').count();
	}

	// ── Tests ──
	// (defined below)
});
```

**Git commit:**
```
git add svelte-frontend/e2e/helpers/seed.ts svelte-frontend/e2e/shelf-status.spec.ts
git commit -m "chore(e2e): shelf test skeleton and seed helpers"
```

---

## Task 2: Three tabs test

Add test inside `test.describe('Shelf page', () => { ... })` block, after the helpers.

```typescript
	test('three tabs show correct cards for each status', async ({ page, authUser, playwright }) => {
		// Seed: one entry per status
		await setupShelf(page, playwright, [
			{ book_slug: BOOKS.H.slug, status: 'WANT_TO_READ' },
			{ book_slug: BOOKS.F.slug, status: 'READING', current_page: 200 },
			{ book_slug: BOOKS.T.slug, status: 'READ' }
		]);

		// Default tab: Want to Read (first tab)
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(1);
		await expect(page.getByText(BOOKS.H.title)).toBeVisible();

		// Switch to Reading tab
		await clickTab(page, 'reading');
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(1);
		await expect(page.getByText(BOOKS.F.title)).toBeVisible();

		// Switch to Read tab
		await clickTab(page, 'read');
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(1);
		await expect(page.getByText(BOOKS.T.title)).toBeVisible();

		// Switch back — still 1
		await clickTab(page, 'want_to_read');
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(1);

		await teardownShelf(page, playwright);
	});
```

**Git commit:**
```
git add svelte-frontend/e2e/shelf-status.spec.ts
git commit -m "test(e2e): three tabs switch correctly with seeded entries"
```

---

## Task 3: StatusDropdown change test

```typescript
	test('changing status via dropdown moves card to target tab', async ({ page, authUser, playwright }) => {
		await setupShelf(page, playwright, [
			{ book_slug: BOOKS.H.slug, status: 'WANT_TO_READ' }
		]);

		// Should be 1 card in Want to Read tab
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(1);

		// Open status dropdown, select "Reading"
		await page.locator('[data-testid="status-dropdown"]').click();
		await page.getByRole('option', { name: 'Reading' }).click();

		// Card should disappear from Want to Read tab
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(0);

		// Switch to Reading tab — card should be there
		await clickTab(page, 'reading');
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(1);
		await expect(page.getByText(BOOKS.H.title)).toBeVisible();

		await teardownShelf(page, playwright);
	});
```

**Git commit:**
```
git add svelte-frontend/e2e/shelf-status.spec.ts
git commit -m "test(e2e): status dropdown change moves card between tabs"
```

---

## Task 4: RatingWidget stars test

```typescript
	test('rating stars update visually on click', async ({ page, authUser, playwright }) => {
		await setupShelf(page, playwright, [
			{ book_slug: BOOKS.H.slug, status: 'WANT_TO_READ' }
		]);

		// Initially no stars selected (rating is null for new entries)
		const stars = page.locator('[data-testid="rating-star"]');
		await expect(stars).toHaveCount(5);
		const selectedBefore = page.locator('[data-testid="rating-star"][data-selected="true"]');
		await expect(selectedBefore).toHaveCount(0);

		// Click star 3 (sets rating = 3)
		await page.locator('[data-testid="rating-star"][data-rating="3"]').click();

		// Stars 1-3 should now be selected
		await expect(
			page.locator('[data-testid="rating-star"][data-selected="true"]')
		).toHaveCount(3);

		// Click star 5 (changes rating = 5)
		await page.locator('[data-testid="rating-star"][data-rating="5"]').click();
		await expect(
			page.locator('[data-testid="rating-star"][data-selected="true"]')
		).toHaveCount(5);

		// Click star 5 again (same star — should clear rating per spec)
		await page.locator('[data-testid="rating-star"][data-rating="5"]').click();
		await expect(
			page.locator('[data-testid="rating-star"][data-selected="true"]')
		).toHaveCount(0);

		await teardownShelf(page, playwright);
	});
```

**Git commit:**
```
git add svelte-frontend/e2e/shelf-status.spec.ts
git commit -m "test(e2e): rating stars update, change, and clear correctly"
```

---

## Task 5: ProgressBar visibility and correctness

```typescript
	test('progress bar visible only in Reading tab with correct values', async ({ page, authUser, playwright }) => {
		await setupShelf(page, playwright, [
			{ book_slug: BOOKS.H.slug, status: 'READING', current_page: 200 },
			{ book_slug: BOOKS.F.slug, status: 'WANT_TO_READ' }
		]);

		// Want to Read tab: progress bar should NOT exist
		// (default tab is the first tab with entries, but we have entries in multiple tabs;
		//  first tab rendered depends on impl. Navigate explicitly.)
		await clickTab(page, 'want_to_read');
		await expect(page.locator('[data-testid="progress-bar"]')).toHaveCount(0);

		// Reading tab: progress bar should be visible with correct data
		await clickTab(page, 'reading');
		const progressBar = page.locator('[data-testid="progress-bar"]');
		await expect(progressBar).toBeVisible();

		// Verify data attributes carry correct values
		await expect(progressBar).toHaveAttribute('data-current', '200');
		await expect(progressBar).toHaveAttribute('data-total', String(BOOKS.H.page_count));

		// Verify text shows fraction
		await expect(progressBar).toContainText(`200 / ${BOOKS.H.page_count}`);

		await teardownShelf(page, playwright);
	});
```

**Git commit:**
```
git add svelte-frontend/e2e/shelf-status.spec.ts
git commit -m "test(e2e): progress bar visible only in Reading tab with correct data"
```

---

## Task 6: Empty states test

```typescript
	test('empty states shown per tab when user has no shelf entries', async ({ page, authUser, playwright }) => {
		// Navigate without seeding any entries
		await page.goto('/shelf');

		// All three tabs should show empty states
		// (most implementations default to Want-to-Read tab)
		const empty = page.locator('[data-testid="shelf-empty"]');
		await expect(empty).toBeVisible();

		// Check Want to Read empty message
		await clickTab(page, 'want_to_read');
		await expect(page.getByText(/no books waiting/i)).toBeVisible();

		// Check Reading empty message
		await clickTab(page, 'reading');
		await expect(page.getByText(/not reading anything/i)).toBeVisible();

		// Check Read empty message
		await clickTab(page, 'read');
		await expect(page.getByText(/no finished books/i)).toBeVisible();

		// No cleanup needed — user has no entries to delete
	});
```

**Git commit:**
```
git add svelte-frontend/e2e/shelf-status.spec.ts
git commit -m "test(e2e): empty states display correctly per tab"
```

---

## Task 7: Cross-user isolation test

```typescript
	test('User B does not see User A shelf entries', async ({ page, authUser, playwright }) => {
		// AuthUser (User A) seeds entries
		await setupShelf(page, playwright, [
			{ book_slug: BOOKS.H.slug, status: 'WANT_TO_READ' },
			{ book_slug: BOOKS.F.slug, status: 'READ' }
		]);

		// User A sees 2 cards on page load
		// (default tab might show only one status — check total by navigating all tabs)
		// Actually, page loads all entries. The default tab shows only one status.
		// We verify User A can see entries exist:
		const wantTabCount = await cardCount(page);
		expect(wantTabCount).toBeGreaterThanOrEqual(1);

		// Logout User A (clear cookies) and login as a fresh user (User B)
		// Register User B via API fixture
		const { user, cookies } = await registerUserB(playwright);
		await page.context().clearCookies();
		await page.context().addCookies(cookies);

		// Navigate to /shelf as User B
		await page.goto('/shelf');

		// User B should see empty states — zero cards across all tabs
		await expect(page.locator('[data-testid="shelf-empty"]')).toBeVisible();
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(0);

		// Cleanup User A's data (reuse stored cookies) and User B (via API)
		// NOTE: We lost User A's auth cookies after clearCookies(). We need to
		// re-login User A or store cookies before clearing. Restructure:
		// — see revised code below that stores cookies before switching users
		await teardownUserB(playwright, cookies, TEST_PASSWORD);
	});

	/**
	 * Register a second user via API and return cookies for browser injection.
	 * Mirrors fixtures.ts registerUser() but adapted for inline use.
	 */
	async function registerUserB(
		playwright: typeof import('@playwright/test').playwright
	): Promise<{ user: { email: string; password: string }; cookies: Cookie[] }> {
		const api = await playwright.request.newContext({ baseURL: API_BASE_URL });
		const email = `userb-${randomUUID().slice(0, 8)}@e2e.example`;
		const password = 'TestPass123!';
		const res = await api.post('/api/auth/register/', {
			data: { email, display_name: 'User B', password }
		});
		if (!res.ok()) throw new Error(`[test] registerUserB failed: ${res.status()} ${await res.text()}`);
		const { cookies } = await api.storageState();
		await api.dispose();
		return { user: { email, password }, cookies };
	}

	async function teardownUserB(
		playwright: typeof import('@playwright/test').playwright,
		cookies: Cookie[],
		password: string
	): Promise<void> {
		const api = await playwright.request.newContext({
			baseURL: API_BASE_URL,
			storageState: { cookies }
		});
		const res = await api.delete('/api/users/me/', { data: { current_password: password } });
		if (!res.ok()) console.warn(`[test] teardownUserB failed: ${res.status()}`);
		await api.dispose();
	}
```

Above has a problem: User A entries won't be cleaned up because we lose User A's cookies. Better approach — restructure the test:

```typescript
	test('User B does not see User A shelf entries', async ({ page, authUser, playwright, api }) => {
		// Store User A cookies before logout
		const userACookies = await page.context().cookies();

		// Seed entries as User A
		await seedShelfEntry(
			{ book_slug: BOOKS.H.slug, status: 'WANT_TO_READ' },
			userACookies,
			playwright
		);
		await seedShelfEntry(
			{ book_slug: BOOKS.F.slug, status: 'READ' },
			userACookies,
			playwright
		);

		// Navigate to /shelf and verify User A sees entries
		await page.goto('/shelf');
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(2);
		// (assuming one tab shows all or we count filtered; depends on default tab. If only WANT_TO_READ tab shows by default, we'd see 1. But the spec says "page loads all entries" with client-side filter. The actual test can assert >= 1.)

		// Register User B and switch browser context
		const { user: userB, cookies: userBCookies } = await registerUserB(playwright);
		await page.context().clearCookies();
		await page.context().addCookies(userBCookies);

		await page.goto('/shelf');

		// User B sees empty — zero cards
		await expect(page.locator('[data-testid="shelf-empty"]')).toBeVisible();
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(0);

		// Switch back to User A cookies for cleanup
		await page.context().clearCookies();
		await page.context().addCookies(userACookies);

		// Cleanup User A entries
		await cleanupShelfEntries(userACookies, playwright);

		// Cleanup User B
		await teardownUserB(playwright, userBCookies, 'TestPass123!');
	});
```

Need to add imports at top of file:
```typescript
import { randomUUID } from 'node:crypto';
import { type Cookie } from '@playwright/test';
```

**Git commit:**
```
git add svelte-frontend/e2e/shelf-status.spec.ts
git commit -m "test(e2e): cross-user shelf entry isolation"
```

---

## Task 8: DELETE shelf entry test

```typescript
	test('deleting a shelf entry removes it from the page', async ({ page, authUser, playwright }) => {
		await setupShelf(page, playwright, [
			{ book_slug: BOOKS.H.slug, status: 'WANT_TO_READ' }
		]);

		// Verify card is present
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(1);

		// Click delete button — inline confirm button appears (no browser dialog)
		await page.locator('[data-testid="shelf-delete-btn"]').click();

		// Click the confirm button to actually delete
		await page.locator('[data-testid="shelf-delete-confirm"]').click();

		// Card should disappear
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(0);

		// Empty state should be visible
		await expect(page.locator('[data-testid="shelf-empty"]')).toBeVisible();

		await teardownShelf(page, playwright);
	});
```

**Git commit:**
```
git add svelte-frontend/e2e/shelf-status.spec.ts
git commit -m "test(e2e): delete shelf entry removes card from view"
```

---

## Task 9: Final verify run + commit

```bash
# Run from svelte-frontend/
npx playwright test e2e/shelf-status.spec.ts
```

Expected output: 7 passed.

If any tests fail:
- Check Django backend is running: `make dev-up`
- Check test books exist in DB (run seeding command if needed)
- Check `data-testid` attributes are on components (verify Phase 3c implemented them)

```bash
git add svelte-frontend/e2e/shelf-status.spec.ts svelte-frontend/e2e/helpers/seed.ts
git commit -m "test(e2e): shelf page E2E tests — 7 cases (tabs, status, rating, progress, empty, isolation, delete)"
```

---

## Complete Final File: `svelte-frontend/e2e/shelf-status.spec.ts`

For reference — the complete merged file after all tasks:

```typescript
// e2e/shelf-status.spec.ts
//
// E2E tests for /shelf — the user's reading shelf page.
// Requires: running Django backend + SvelteKit dev server.
// Run: npx playwright test e2e/shelf-status.spec.ts

import { randomUUID } from 'node:crypto';
import { type Cookie } from '@playwright/test';
import { test, expect, API_BASE_URL } from './fixtures';
import {
	seedShelfEntry,
	cleanupShelfEntries,
	type SeedShelfEntry
} from './helpers/seed';

const TEST_PASSWORD = 'TestPass123!';

// Test books that must exist in the dev database (seeded by make dev-up / management command).
const BOOKS = {
	H: { slug: 'the-hobbit', title: 'The Hobbit', page_count: 423 },
	F: { slug: 'the-fellowship-of-the-ring', title: 'The Fellowship of the Ring', page_count: 531 },
	T: { slug: 'the-two-towers', title: 'The Two Towers', page_count: 415 }
} as const;

// ── User B helpers (for cross-user isolation test) ──

async function registerUserB(
	playwright: typeof import('@playwright/test').playwright
): Promise<{ user: { email: string; password: string }; cookies: Cookie[] }> {
	const api = await playwright.request.newContext({ baseURL: API_BASE_URL });
	const email = `userb-${randomUUID().slice(0, 8)}@e2e.example`;
	const password = TEST_PASSWORD;
	const res = await api.post('/api/auth/register/', {
		data: { email, display_name: 'User B', password }
	});
	if (!res.ok()) {
		const body = await res.text();
		await api.dispose();
		throw new Error(`[test] registerUserB failed: ${res.status()} ${body}`);
	}
	const { cookies } = await api.storageState();
	await api.dispose();
	return { user: { email, password }, cookies };
}

async function teardownUserB(
	playwright: typeof import('@playwright/test').playwright,
	cookies: Cookie[],
	password: string
): Promise<void> {
	const api = await playwright.request.newContext({
		baseURL: API_BASE_URL,
		storageState: { cookies }
	});
	const res = await api.delete('/api/users/me/', { data: { current_password: password } });
	if (!res.ok()) {
		console.warn(`[test] teardownUserB failed: ${res.status()} ${await res.text()}`);
	}
	await api.dispose();
}

test.describe('Shelf page', () => {
	// ── Helpers ──

	async function setupShelf(
		page: import('@playwright/test').Page,
		playwright: typeof import('@playwright/test').playwright,
		entries: { book_slug: string; status: string; current_page?: number | null }[]
	): Promise<SeedShelfEntry[]> {
		const cookies = await page.context().cookies();
		const seeded: SeedShelfEntry[] = [];
		for (const e of entries) {
			const result = await seedShelfEntry(e, cookies, playwright);
			seeded.push(result);
		}
		await page.goto('/shelf');
		return seeded;
	}

	async function teardownShelf(
		page: import('@playwright/test').Page,
		playwright: typeof import('@playwright/test').playwright
	): Promise<void> {
		const cookies = await page.context().cookies();
		await cleanupShelfEntries(cookies, playwright);
	}

	async function clickTab(
		page: import('@playwright/test').Page,
		tab: 'want_to_read' | 'reading' | 'read'
	) {
		await page.locator(`[data-testid="shelf-tab"][data-tab="${tab}"]`).click();
	}

	// ── Task 2: Three tabs ──

	test('three tabs show correct cards for each status', async ({ page, authUser, playwright }) => {
		await setupShelf(page, playwright, [
			{ book_slug: BOOKS.H.slug, status: 'WANT_TO_READ' },
			{ book_slug: BOOKS.F.slug, status: 'READING', current_page: 200 },
			{ book_slug: BOOKS.T.slug, status: 'READ' }
		]);

		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(1);
		await expect(page.getByText(BOOKS.H.title)).toBeVisible();

		await clickTab(page, 'reading');
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(1);
		await expect(page.getByText(BOOKS.F.title)).toBeVisible();

		await clickTab(page, 'read');
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(1);
		await expect(page.getByText(BOOKS.T.title)).toBeVisible();

		await clickTab(page, 'want_to_read');
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(1);

		await teardownShelf(page, playwright);
	});

	// ── Task 3: StatusDropdown change ──

	test('changing status via dropdown moves card to target tab', async ({ page, authUser, playwright }) => {
		await setupShelf(page, playwright, [
			{ book_slug: BOOKS.H.slug, status: 'WANT_TO_READ' }
		]);

		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(1);

		await page.locator('[data-testid="status-dropdown"]').click();
		await page.getByRole('option', { name: 'Reading' }).click();

		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(0);

		await clickTab(page, 'reading');
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(1);
		await expect(page.getByText(BOOKS.H.title)).toBeVisible();

		await teardownShelf(page, playwright);
	});

	// ── Task 4: RatingWidget ──

	test('rating stars update visually on click', async ({ page, authUser, playwright }) => {
		await setupShelf(page, playwright, [
			{ book_slug: BOOKS.H.slug, status: 'WANT_TO_READ' }
		]);

		const stars = page.locator('[data-testid="rating-star"]');
		await expect(stars).toHaveCount(5);
		await expect(page.locator('[data-testid="rating-star"][data-selected="true"]')).toHaveCount(0);

		await page.locator('[data-testid="rating-star"][data-rating="3"]').click();
		await expect(page.locator('[data-testid="rating-star"][data-selected="true"]')).toHaveCount(3);

		await page.locator('[data-testid="rating-star"][data-rating="5"]').click();
		await expect(page.locator('[data-testid="rating-star"][data-selected="true"]')).toHaveCount(5);

		// Same star again → clear rating
		await page.locator('[data-testid="rating-star"][data-rating="5"]').click();
		await expect(page.locator('[data-testid="rating-star"][data-selected="true"]')).toHaveCount(0);

		await teardownShelf(page, playwright);
	});

	// ── Task 5: ProgressBar ──

	test('progress bar visible only in Reading tab with correct values', async ({ page, authUser, playwright }) => {
		await setupShelf(page, playwright, [
			{ book_slug: BOOKS.H.slug, status: 'READING', current_page: 200 },
			{ book_slug: BOOKS.F.slug, status: 'WANT_TO_READ' }
		]);

		await clickTab(page, 'want_to_read');
		await expect(page.locator('[data-testid="progress-bar"]')).toHaveCount(0);

		await clickTab(page, 'reading');
		const progressBar = page.locator('[data-testid="progress-bar"]');
		await expect(progressBar).toBeVisible();
		await expect(progressBar).toHaveAttribute('data-current', '200');
		await expect(progressBar).toHaveAttribute('data-total', String(BOOKS.H.page_count));
		await expect(progressBar).toContainText(`200 / ${BOOKS.H.page_count}`);

		await teardownShelf(page, playwright);
	});

	// ── Task 6: Empty states ──

	test('empty states shown per tab when user has no shelf entries', async ({ page, authUser }) => {
		await page.goto('/shelf');

		await expect(page.locator('[data-testid="shelf-empty"]')).toBeVisible();

		await clickTab(page, 'want_to_read');
		await expect(page.getByText(/no books waiting/i)).toBeVisible();

		await clickTab(page, 'reading');
		await expect(page.getByText(/not reading anything/i)).toBeVisible();

		await clickTab(page, 'read');
		await expect(page.getByText(/no finished books/i)).toBeVisible();
	});

	// ── Task 7: Cross-user isolation ──

	test('User B does not see User A shelf entries', async ({ page, authUser, playwright }) => {
		// Store User A cookies before any operations
		const userACookies = await page.context().cookies();

		await seedShelfEntry(
			{ book_slug: BOOKS.H.slug, status: 'WANT_TO_READ' },
			userACookies,
			playwright
		);
		await seedShelfEntry(
			{ book_slug: BOOKS.F.slug, status: 'READ' },
			userACookies,
			playwright
		);

		// Verify User A sees entries
		await page.goto('/shelf');
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(2);

		// Register User B and switch context
		const { cookies: userBCookies } = await registerUserB(playwright);
		await page.context().clearCookies();
		await page.context().addCookies(userBCookies);

		await page.goto('/shelf');
		await expect(page.locator('[data-testid="shelf-empty"]')).toBeVisible();
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(0);

		// Switch back to User A for cleanup
		await page.context().clearCookies();
		await page.context().addCookies(userACookies);

		await cleanupShelfEntries(userACookies, playwright);

		// Cleanup User B
		await teardownUserB(playwright, userBCookies, TEST_PASSWORD);
	});

	// ── Task 8: DELETE ──

	test('deleting a shelf entry removes it from the page', async ({ page, authUser, playwright }) => {
		await setupShelf(page, playwright, [
			{ book_slug: BOOKS.H.slug, status: 'WANT_TO_READ' }
		]);

		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(1);

		// Click delete → confirm appears (inline, no browser dialog)
		await page.locator('[data-testid="shelf-delete-btn"]').click();
		await page.locator('[data-testid="shelf-delete-confirm"]').click();

		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="shelf-empty"]')).toBeVisible();

		await teardownShelf(page, playwright);
	});
});
```

---

## Dependencies & Assumptions

| What | Who | When |
|---|---|---|
| `data-testid` attributes on components | Phase 3c frontend | Before running 3d |
| Books in dev DB (slugs: `the-hobbit`, `the-fellowship-of-the-ring`, `the-two-towers`) | `manage.py seed_books` in dev setup | Before first run — add pre-test assertion: `GET /api/books/?slug=the-hobbit` returns 200 |
| `GET/POST /api/shelf/entries/` | Phase 3b backend | Before running 3d |
| `PUT /api/ratings/` | Phase 3a backend | Before running 3d |
| `PATCH/DELETE /api/shelf/entries/{id}/` | Phase 3b backend | Before running 3d |

## Key Patterns Used

| Pattern | Source |
|---|---|
| Import `test`, `expect`, `API_BASE_URL` from `./fixtures` | auth.spec.ts, settings.spec.ts |
| `authUser` fixture for logged-in browser context | all specs |
| `playwright.request.newContext({ storageState: { cookies } })` for API calls | auth.spec.ts L26, fixtures.ts L123 |
| `page.getByRole('option', { name })` for dropdown options | settings.spec.ts |
| `page.locator('[data-testid="..."]')` chained with `.click()`, `.toHaveCount()` | profile.spec.ts |
| `page.getByText(/regex/i)` for text matching | settings.spec.ts, auth.spec.ts |
| `test.describe('...', () => { ... })` block organization | all specs |
| `baseURL: 'http://localhost:5174'` from playwright.config.ts | config |
| No `test.beforeAll` — data seeded per-test | (new pattern) |
