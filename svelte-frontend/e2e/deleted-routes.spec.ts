import { test, expect } from './fixtures';

// Routes that should return 404 — /discover and /books/* were here before
// Phase 2c/2d but are now live pages.
const deletedRoutes = ['/shelf', '/this-does-not-exist-at-all'];

test.describe('Deleted routes return 404', () => {
	for (const route of deletedRoutes) {
		test(`${route} returns 404`, async ({ page }) => {
			const res = await page.goto(route);
			expect(res?.status()).toBe(404);
		});
	}

	test('+error.svelte is rendered for 404', async ({ page }) => {
		await page.goto('/this-does-not-exist-at-all');
		await expect(page.getByRole('link', { name: 'Go home' })).toBeVisible();
	});
});
