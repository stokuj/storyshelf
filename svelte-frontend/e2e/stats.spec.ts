// Reading stats (M9) E2E. Requires the dev stack up (Django :8000 + seeded books)
// and the Vite `/api` proxy (default — see ADR-002). A full run registers several
// users; relax the register throttle with `THROTTLE_AUTH_REGISTER=1000/min` (env,
// no code change). Run with `npm run test:e2e`. Not part of CI / `make verify`.
import { type Cookie, type Page } from '@playwright/test';
import { test, expect, API_BASE_URL } from './fixtures';
import { seedShelfEntry, cleanupShelfEntries } from './helpers/seed';

const BOOK = { slug: 'the-hobbit', title: 'The Hobbit', page_count: 423 } as const;

async function gotoReady(page: Page, url: string) {
	await page.goto(url);
	await page.waitForLoadState('networkidle');
}

async function seedRating(
	book_slug: string,
	rating: number,
	cookies: Cookie[],
	playwright: typeof import('@playwright/test').playwright
): Promise<void> {
	const api = await playwright.request.newContext({
		baseURL: API_BASE_URL,
		storageState: { cookies, origins: [] }
	});
	const res = await api.put('/api/ratings/', { data: { book_slug, rating } });
	if (!res.ok()) {
		const body = await res.text();
		await api.dispose();
		throw new Error(`[seed] rating failed: ${res.status()} ${body}`);
	}
	await api.dispose();
}

async function cleanupRatings(
	cookies: Cookie[],
	playwright: typeof import('@playwright/test').playwright
): Promise<void> {
	const api = await playwright.request.newContext({
		baseURL: API_BASE_URL,
		storageState: { cookies, origins: [] }
	});
	const res = await api.get('/api/ratings/');
	if (res.ok()) {
		const ratings: { id: number }[] = await res.json();
		for (const r of ratings) await api.delete(`/api/ratings/${r.id}/`);
	}
	await api.dispose();
}

test.describe('Reading stats', () => {
	test('anonymous visit to /stats redirects to /login', async ({ page }) => {
		await page.goto('/stats');
		await expect(page).toHaveURL(/\/login/);
	});

	test('empty user sees zeros, dashes, and a "No data yet" chart', async ({ page, authUser }) => {
		await gotoReady(page, '/stats');

		await expect(page.getByTestId('stat-read')).toHaveText('0');
		await expect(page.getByTestId('stat-pages-read')).toHaveText('0');
		await expect(page.getByTestId('stat-avg-rating')).toHaveText('—');
		await expect(page.getByTestId('stat-time-on-shelf')).toHaveText('—');

		// Books-per-year has no data → empty branch; rating chart always renders 5 buckets.
		await expect(page.getByTestId('chart-books-per-year').getByText('No data yet')).toBeVisible();
		await expect(page.getByTestId('chart-rating').getByTestId('bar')).toHaveCount(5);
	});

	test('marking a book READ and rating it is reflected in stats', async ({
		page,
		authUser,
		playwright
	}) => {
		const cookies = await page.context().cookies();
		// POST through the API auto-sets finish_date (status READ) → books-per-year gets data.
		await seedShelfEntry({ book_slug: BOOK.slug, status: 'READ' }, cookies, playwright);
		await seedRating(BOOK.slug, 4, cookies, playwright);

		await gotoReady(page, '/stats');

		await expect(page.getByTestId('stat-read')).toHaveText('1');
		await expect(page.getByTestId('stat-pages-read')).toHaveText(String(BOOK.page_count));
		await expect(page.getByTestId('stat-avg-rating')).toHaveText('4');

		// One finished book this year → exactly one bar, no empty message.
		await expect(page.getByTestId('chart-books-per-year').getByText('No data yet')).toHaveCount(0);
		await expect(page.getByTestId('chart-books-per-year').getByTestId('bar')).toHaveCount(1);

		await cleanupShelfEntries(cookies, playwright);
		await cleanupRatings(cookies, playwright);
	});
});
