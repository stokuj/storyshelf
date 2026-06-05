// Social feed (M12) E2E. Requires the dev stack up (Django :8000 + seeded books) and
// the Vite `/api` proxy (ADR-002). Relax the register throttle on the server with
// `THROTTLE_AUTH_REGISTER=1000/min`. Run with `npm run test:e2e`. Not part of CI.
import { type APIRequestContext, type Cookie, type Page } from '@playwright/test';
import { API_BASE_URL, test, expect, TEST_PASSWORD } from './fixtures';
import { cleanupMyReview } from './helpers/seed';

async function gotoReady(page: Page, url: string) {
	await page.goto(url);
	await page.waitForLoadState('networkidle');
}

/** Authenticated API context for an existing user (logs in to get cookies). */
async function apiAs(
	playwright: typeof import('@playwright/test').playwright,
	email: string
): Promise<APIRequestContext> {
	const api = await playwright.request.newContext({ baseURL: API_BASE_URL });
	const res = await api.post('/api/auth/login/', { data: { email, password: TEST_PASSWORD } });
	if (!res.ok()) {
		const body = await res.text();
		await api.dispose();
		throw new Error(`[social-feed] login failed for ${email}: ${res.status()} ${body}`);
	}
	return api;
}

/** Slug of the first seeded book (global-setup guarantees at least three). */
async function firstBookSlug(api: APIRequestContext): Promise<string> {
	const res = await api.get('/api/books/?per_page=1');
	const data = await res.json();
	return data.data[0].slug;
}

/** Follow a user via API using the logged-in browser's cookies. */
async function followViaApi(
	playwright: typeof import('@playwright/test').playwright,
	cookies: Cookie[],
	handle: string
): Promise<void> {
	const api = await playwright.request.newContext({
		baseURL: API_BASE_URL,
		storageState: { cookies, origins: [] }
	});
	await api.post(`/api/u/${handle}/follow/`);
	await api.dispose();
}

test.describe('Social feed (M12)', () => {
	test('feed shows a followed public user activity', async ({
		page,
		authUser,
		guestUser,
		playwright
	}) => {
		// Seed a review authored by the public guestUser.
		const guestApi = await apiAs(playwright, guestUser.email);
		const slug = await firstBookSlug(guestApi);
		await guestApi.put('/api/reviews/', { data: { book_slug: slug, body: 'Loved this one.' } });
		await guestApi.dispose();

		// authUser follows guestUser, then opens the feed.
		await followViaApi(playwright, await page.context().cookies(), guestUser.handle);
		await gotoReady(page, '/feed');

		const item = page.getByTestId('feed-item').first();
		await expect(item).toBeVisible();
		await expect(item).toContainText(guestUser.displayName);

		// Cleanup the seeded review.
		const guestApi2 = await apiAs(playwright, guestUser.email);
		await cleanupMyReview(slug, (await guestApi2.storageState()).cookies as Cookie[], playwright);
		await guestApi2.dispose();
	});

	test('logged-in user can like a review', async ({ page, authUser, playwright }) => {
		const api = await apiAs(playwright, authUser.email);
		const slug = await firstBookSlug(api);
		await api.dispose();

		await gotoReady(page, `/books/${slug}`);
		await page.getByTestId('review-textarea').fill('A review to be liked.');
		await page.getByRole('button', { name: /post review/i }).click();
		await expect(page.getByTestId('review-card')).toContainText('A review to be liked.');

		const likeBtn = page.getByTestId('like-button').first();
		const likeCount = page.getByTestId('like-count').first();
		await expect(likeCount).toHaveText('0');
		await Promise.all([
			page.waitForResponse((r) => r.url().includes('/like/') && r.request().method() === 'POST'),
			likeBtn.click()
		]);
		await expect(likeCount).toHaveText('1');

		await cleanupMyReview(slug, await page.context().cookies(), playwright);
	});

	test('public profile shows the Reviews section', async ({
		page,
		authUser,
		guestUser,
		playwright
	}) => {
		const guestApi = await apiAs(playwright, guestUser.email);
		const slug = await firstBookSlug(guestApi);
		await guestApi.put('/api/reviews/', { data: { book_slug: slug, body: 'On my profile.' } });
		const cookies = (await guestApi.storageState()).cookies as Cookie[];
		await guestApi.dispose();

		await gotoReady(page, `/u/${guestUser.handle}`);
		await expect(page.getByRole('heading', { name: 'Reviews' })).toBeVisible();
		await expect(page.getByTestId('review-card').first()).toContainText('On my profile.');

		await cleanupMyReview(slug, cookies, playwright);
	});
});
