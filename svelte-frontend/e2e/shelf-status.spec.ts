// Shelf (M3) E2E. Requires the dev stack up (Django :8000 + seeded books) and the
// Vite `/api` proxy (default — see ADR-002) so client-side mutations reach Django.
// A full run registers several users; relax the register throttle on the Django
// server with `THROTTLE_AUTH_REGISTER=1000/min` (env, no code change). Run with
// `npm run test:e2e`. Not part of CI / `make verify`.
import { randomUUID } from 'node:crypto';
import { type Cookie, type Page } from '@playwright/test';
import { test, expect, API_BASE_URL } from './fixtures';
import { seedShelfEntry, cleanupShelfEntries } from './helpers/seed';

const BOOKS = {
	H: { slug: 'the-hobbit', title: 'The Hobbit', page_count: 423 },
	F: { slug: 'the-fellowship-of-the-ring', title: 'The Fellowship of the Ring' },
	T: { slug: 'the-two-towers', title: 'The Two Towers' }
} as const;

// Navigate and wait for the client bundle to settle, so Svelte has hydrated and
// click handlers are attached before we interact (avoids clicking a server-rendered
// button before its `onclick` exists).
async function gotoReady(page: Page, url: string) {
	await page.goto(url);
	await page.waitForLoadState('networkidle');
}

async function clickTab(page: Page, tab: 'want_to_read' | 'reading' | 'read') {
	await page.locator(`[data-testid="shelf-tab"][data-tab="${tab}"]`).click();
}

test.describe('Shelf', () => {
	test('anonymous visit to /shelf redirects to /login', async ({ page }) => {
		await page.goto('/shelf');
		await expect(page).toHaveURL(/\/login/);
	});

	test('add to shelf from book detail, then it appears on /shelf', async ({
		page,
		authUser,
		playwright
	}) => {
		await gotoReady(page, `/books/${BOOKS.H.slug}`);
		await page.locator('[data-testid="add-to-shelf"]').click();
		await expect(page.locator('[data-testid="shelf-control"]')).toBeVisible();

		await page.goto('/shelf');
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(1);
		await expect(page.locator('[data-testid="shelf-book-card"]')).toContainText(BOOKS.H.title);

		await cleanupShelfEntries(await page.context().cookies(), playwright);
	});

	test('three tabs filter by status', async ({ page, authUser, playwright }) => {
		const cookies = await page.context().cookies();
		await seedShelfEntry({ book_slug: BOOKS.H.slug, status: 'WANT_TO_READ' }, cookies, playwright);
		await seedShelfEntry(
			{ book_slug: BOOKS.F.slug, status: 'READING', current_page: 200 },
			cookies,
			playwright
		);
		await seedShelfEntry({ book_slug: BOOKS.T.slug, status: 'READ' }, cookies, playwright);
		await gotoReady(page, '/shelf');

		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(1);
		await clickTab(page, 'reading');
		await expect(page.locator('[data-testid="shelf-book-card"]')).toContainText(BOOKS.F.title);
		await clickTab(page, 'read');
		await expect(page.locator('[data-testid="shelf-book-card"]')).toContainText(BOOKS.T.title);

		await cleanupShelfEntries(cookies, playwright);
	});

	test('status dropdown moves card between tabs', async ({ page, authUser, playwright }) => {
		const cookies = await page.context().cookies();
		await seedShelfEntry({ book_slug: BOOKS.H.slug, status: 'WANT_TO_READ' }, cookies, playwright);
		await gotoReady(page, '/shelf');

		await page.locator('[data-testid="status-dropdown"]').first().click();
		await page.getByRole('option', { name: 'Reading' }).click();
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(0);
		await clickTab(page, 'reading');
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(1);

		await cleanupShelfEntries(cookies, playwright);
	});

	test('rating stars set, change, and clear', async ({ page, authUser, playwright }) => {
		const cookies = await page.context().cookies();
		await seedShelfEntry({ book_slug: BOOKS.H.slug, status: 'WANT_TO_READ' }, cookies, playwright);
		await gotoReady(page, '/shelf');

		const selected = page.locator('[data-testid="rating-star"][data-selected="true"]');
		await expect(selected).toHaveCount(0);
		await page.locator('[data-testid="rating-star"][data-rating="3"]').click();
		await expect(selected).toHaveCount(3);
		await page.locator('[data-testid="rating-star"][data-rating="5"]').click();
		await expect(selected).toHaveCount(5);
		await page.locator('[data-testid="rating-star"][data-rating="5"]').click();
		await expect(selected).toHaveCount(0);

		await cleanupShelfEntries(cookies, playwright);
	});

	test('progress bar shows only in Reading tab with correct values', async ({
		page,
		authUser,
		playwright
	}) => {
		const cookies = await page.context().cookies();
		await seedShelfEntry(
			{ book_slug: BOOKS.H.slug, status: 'READING', current_page: 200 },
			cookies,
			playwright
		);
		await gotoReady(page, '/shelf');

		await clickTab(page, 'want_to_read');
		await expect(page.locator('[data-testid="progress-bar"]')).toHaveCount(0);
		await clickTab(page, 'reading');
		const bar = page.locator('[data-testid="progress-bar"]');
		await expect(bar).toBeVisible();
		await expect(bar).toHaveAttribute('data-current', '200');
		await expect(bar).toHaveAttribute('data-total', String(BOOKS.H.page_count));

		await cleanupShelfEntries(cookies, playwright);
	});

	test('user can set reading progress', async ({ page, authUser, playwright }) => {
		const cookies = await page.context().cookies();
		await seedShelfEntry(
			{ book_slug: BOOKS.H.slug, status: 'READING', current_page: 100 },
			cookies,
			playwright
		);
		await gotoReady(page, '/shelf?tab=reading');

		const input = page.getByTestId('current-page-input').first();
		await input.fill('42');
		await input.blur();
		await expect(page.getByTestId('progress-bar').first()).toHaveAttribute('data-current', '42');

		await cleanupShelfEntries(cookies, playwright);
	});

	test('empty states per tab when shelf is empty', async ({ page, authUser }) => {
		await gotoReady(page, '/shelf');
		await expect(page.locator('[data-testid="shelf-empty"]')).toBeVisible();
		await clickTab(page, 'reading');
		await expect(page.getByText(/not reading anything/i)).toBeVisible();
		await clickTab(page, 'read');
		await expect(page.getByText(/no finished books/i)).toBeVisible();
	});

	test('user B does not see user A entries', async ({ page, authUser, playwright }) => {
		const aCookies = await page.context().cookies();
		await seedShelfEntry({ book_slug: BOOKS.H.slug, status: 'WANT_TO_READ' }, aCookies, playwright);
		await gotoReady(page, '/shelf');
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(1);

		// Register a fresh user B, swap cookies in the same browser context.
		const api = await playwright.request.newContext({ baseURL: API_BASE_URL });
		const email = `userb-${randomUUID().slice(0, 8)}@e2e.example`;
		const handle = `b${(randomUUID() + randomUUID()).replace(/[^a-f]/g, '')}`.slice(0, 30);
		const reg = await api.post('/api/auth/register/', {
			data: { email, display_name: 'User B', password: 'TestPass123!', handle }
		});
		expect(reg.ok()).toBe(true);
		const { cookies: bCookies } = await api.storageState();
		await api.dispose();

		await page.context().clearCookies();
		await page.context().addCookies(bCookies as Cookie[]);
		await gotoReady(page, '/shelf');
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="shelf-empty"]')).toBeVisible();

		// Cleanup: user B via its own cookies; user A entries via stored A cookies.
		await cleanupShelfEntries(aCookies, playwright);
		const apiB = await playwright.request.newContext({
			baseURL: API_BASE_URL,
			storageState: { cookies: bCookies, origins: [] }
		});
		await apiB.delete('/api/users/me/', { data: { current_password: 'TestPass123!' } });
		await apiB.dispose();
	});
});
