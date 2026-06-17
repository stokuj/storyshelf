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

	test('renders 5 seeded book cards', async ({ page }) => {
		// Book title h3s are inside the grid; EmptyState h3 is outside
		const bookTitles = page.locator('.grid h3');
		await expect(bookTitles).toHaveCount(5);
		await expect(page.getByText('The Fellowship of the Ring')).toBeVisible();
		await expect(page.getByText('Dune')).toBeVisible();
		await expect(page.getByText('1984')).toBeVisible();
	});

	test('search filters books by title', async ({ page }) => {
		const searchInput = page.locator('input[placeholder="Search books…"]');
		// pressSequentially triggers oninput events (fill() does not in SvelteKit)
		await searchInput.click();
		await searchInput.pressSequentially('Fellowship', { delay: 50 });
		// Wait for the (debounced) search to actually apply before counting — guards
		// against typing before the input's oninput handler has hydrated.
		await expect(page).toHaveURL(/q=Fellowship/);
		await expect(page.locator('.grid h3')).toHaveCount(1);
		// Scope to the card heading; the cover fallback also renders the title text.
		await expect(page.locator('.grid h3', { hasText: 'The Fellowship of the Ring' })).toBeVisible();
	});

	test('search empty state shows "No books found"', async ({ page }) => {
		const searchInput = page.locator('input[placeholder="Search books…"]');
		await searchInput.click();
		await searchInput.pressSequentially('xyznonexistentbook123', { delay: 50 });
		await expect(page.getByText('No books found')).toBeVisible();
		await expect(page.locator('.grid h3')).toHaveCount(0);
	});

	test('genre filter shows only matching book', async ({ page }) => {
		// Dropdown is client-only; retry the open until hydration attaches onclick.
		const listbox = page.getByRole('listbox');
		await expect(async () => {
			if (!(await listbox.isVisible())) await page.getByRole('button', { name: 'Genre' }).click();
			await expect(listbox).toBeVisible({ timeout: 500 });
		}).toPass({ timeout: 10_000 });
		await listbox.getByText('fantasy').click();
		// Fellowship + The Hobbit + The Two Towers (all seeded as Fantasy)
		await expect(page.locator('.grid h3')).toHaveCount(3);
	});

	test('sort by rating changes book order', async ({ page }) => {
		// Default ordering is by title — "1984" first alphabetically
		const firstBefore = await page.locator('.grid h3').first().textContent();
		// Dropdown is client-only; retry the open until hydration attaches onclick.
		const listbox = page.getByRole('listbox');
		await expect(async () => {
			if (!(await listbox.isVisible())) await page.getByRole('button', { name: 'Sort' }).click();
			await expect(listbox).toBeVisible({ timeout: 500 });
		}).toPass({ timeout: 10_000 });
		await listbox.getByText('Rating').click();
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

	test('clearing search resets to all seeded books', async ({ page }) => {
		const searchInput = page.locator('input[placeholder="Search books…"]');
		await searchInput.click();
		await searchInput.pressSequentially('Fellowship', { delay: 50 });
		await expect(page.locator('.grid h3')).toHaveCount(1);
		// Clear the input with triple-click + Delete
		await searchInput.click({ clickCount: 3 });
		await searchInput.press('Delete');
		await expect(page.locator('.grid h3')).toHaveCount(5);
	});

	test('navbar search updates results while already on /discover', async ({ page }) => {
		await page.goto('/discover');
		await page.waitForSelector('.grid h3');
		await page.setViewportSize({ width: 1280, height: 800 }); // navbar search is hidden below sm
		const navSearch = page.locator('header').getByRole('searchbox', { name: 'Search books' });
		await navSearch.click();
		await navSearch.pressSequentially('Dune', { delay: 50 });
		await navSearch.press('Enter');
		await expect(page).toHaveURL(/\/discover\?q=Dune/);
		await expect(page.locator('.grid h3', { hasText: 'Dune' })).toBeVisible();
		await expect(page.locator('.grid h3')).toHaveCount(1);
	});
});
