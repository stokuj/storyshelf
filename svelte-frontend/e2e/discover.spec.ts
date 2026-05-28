import { test, expect } from './fixtures';
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const slugsPath = resolve(__dirname, '.seed-slugs.json');
try {
	JSON.parse(readFileSync(slugsPath, 'utf-8'));
} catch {
	throw new Error('Missing .seed-slugs.json — run global setup first.');
}

test.describe('Discover page', () => {
	test.beforeEach(async ({ page }) => {
		await page.goto('/discover');
		// Wait for book cards to appear (SSR + hydration complete)
		await page.waitForSelector('.grid h3', { timeout: 10_000 });
	});

	test('renders 3 book cards', async ({ page }) => {
		// Book title h3s are inside the grid; EmptyState h3 is outside
		const bookTitles = page.locator('.grid h3');
		await expect(bookTitles).toHaveCount(3);
		await expect(page.getByText('The Fellowship of the Ring')).toBeVisible();
		await expect(page.getByText('Dune')).toBeVisible();
		await expect(page.getByText('1984')).toBeVisible();
	});

	test('search filters books by title', async ({ page }) => {
		const searchInput = page.locator('input[placeholder="Search books…"]');
		// pressSequentially triggers oninput events (fill() does not in SvelteKit)
		await searchInput.click();
		await searchInput.pressSequentially('Fellowship', { delay: 50 });
		// expect() retries automatically (up to expect.timeout = 10s) — no waitForTimeout needed
		await expect(page.locator('.grid h3')).toHaveCount(1);
		await expect(page.getByText('The Fellowship of the Ring')).toBeVisible();
		await expect(page.getByText('Dune')).not.toBeVisible();
		await expect(page.getByText('1984')).not.toBeVisible();
	});

	test('search empty state shows "No books found"', async ({ page }) => {
		const searchInput = page.locator('input[placeholder="Search books…"]');
		await searchInput.click();
		await searchInput.pressSequentially('xyznonexistentbook123', { delay: 50 });
		await expect(page.getByText('No books found')).toBeVisible();
		await expect(page.locator('.grid h3')).toHaveCount(0);
	});

	test('genre filter shows only matching book', async ({ page }) => {
		// Genres stored lowercase in DB; dropdown opens after click
		await page.getByRole('button', { name: 'Genre' }).click();
		// Wait for the listbox to appear with at least one option before selecting
		const listbox = page.getByRole('listbox');
		await listbox.waitFor({ state: 'visible', timeout: 5_000 });
		await listbox.getByText('fantasy').click();
		await expect(page.locator('.grid h3')).toHaveCount(1);
		await expect(page.getByText('The Fellowship of the Ring')).toBeVisible();
	});

	test('sort by rating changes book order', async ({ page }) => {
		// Default ordering is by title — "1984" first alphabetically
		const firstBefore = await page.locator('.grid h3').first().textContent();
		// Sort options are hardcoded (not fetched) — no wait needed before click
		await page.getByRole('button', { name: 'Sort' }).click();
		await page.getByRole('listbox').waitFor({ state: 'visible', timeout: 5_000 });
		await page.getByRole('listbox').getByText('Rating').click();
		// Fellowship has avg_rating 4.5 (highest in seed) — should be first after sort
		await expect(page.locator('.grid h3').first()).toHaveText('The Fellowship of the Ring');
		expect(firstBefore).not.toBe('The Fellowship of the Ring');
	});

	test('search input syncs with URL query param', async ({ page }) => {
		const searchInput = page.locator('input[placeholder="Search books…"]');
		await searchInput.click();
		await searchInput.pressSequentially('Fellowship', { delay: 50 });
		await expect(page).toHaveURL(/\/discover\?q=Fellowship/);
	});

	test('clearing search resets to all 3 books', async ({ page }) => {
		const searchInput = page.locator('input[placeholder="Search books…"]');
		await searchInput.click();
		await searchInput.pressSequentially('Fellowship', { delay: 50 });
		await expect(page.locator('.grid h3')).toHaveCount(1);
		// Clear the input with triple-click + Delete
		await searchInput.click({ clickCount: 3 });
		await searchInput.press('Delete');
		await expect(page.locator('.grid h3')).toHaveCount(3);
	});
});
