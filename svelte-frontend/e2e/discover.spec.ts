import { test, expect } from './fixtures';
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const slugsPath = resolve(__dirname, '.seed-slugs.json');
let slugs: Record<string, string>;
try {
	slugs = JSON.parse(readFileSync(slugsPath, 'utf-8'));
} catch {
	throw new Error('Missing .seed-slugs.json — run global setup first.');
}
// Keep reference to avoid "unused variable" lint warning
void slugs;

/** Wait for genres to be fetched (they load client-side after initial render). */
async function waitForGenresLoaded(page: import('@playwright/test').Page) {
	// The genre button is initialised with text "Genre"; wait for it to still say "Genre"
	// AND for at least one option to appear in the listbox after a click.
	// Simpler: just wait a fixed time for the client-side fetch to complete.
	await page.waitForTimeout(1_200);
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
		await page.waitForTimeout(100);
		await searchInput.pressSequentially('Fellowship', { delay: 50 });
		// Debounce is 300 ms + network request
		await page.waitForTimeout(1_500);
		const bookTitles = page.locator('.grid h3');
		await expect(bookTitles).toHaveCount(1);
		await expect(page.getByText('The Fellowship of the Ring')).toBeVisible();
		await expect(page.getByText('Dune')).not.toBeVisible();
		await expect(page.getByText('1984')).not.toBeVisible();
	});

	test('search empty state shows "No books found"', async ({ page }) => {
		const searchInput = page.locator('input[placeholder="Search books…"]');
		await searchInput.click();
		await page.waitForTimeout(100);
		await searchInput.pressSequentially('xyznonexistentbook123', { delay: 50 });
		await page.waitForTimeout(1_500);
		await expect(page.getByText('No books found')).toBeVisible();
		await expect(page.locator('.grid h3')).toHaveCount(0);
	});

	test('genre filter shows only matching book', async ({ page }) => {
		// Wait for client-side genre fetch to complete
		await waitForGenresLoaded(page);
		// The genre dropdown is a custom <button>; genres are stored lowercase in the DB
		await page.getByRole('button', { name: 'Genre' }).click();
		// Wait for the listbox to appear and select fantasy
		await page.getByRole('listbox').waitFor({ state: 'visible', timeout: 5_000 });
		await page.getByRole('listbox').getByText('fantasy').click();
		await page.waitForTimeout(1_200);
		const bookTitles = page.locator('.grid h3');
		await expect(bookTitles).toHaveCount(1);
		await expect(page.getByText('The Fellowship of the Ring')).toBeVisible();
	});

	test('sort by rating changes book order', async ({ page }) => {
		// Default ordering is by title, so "1984" should be first alphabetically
		await waitForGenresLoaded(page);
		const firstBefore = await page.locator('.grid h3').first().textContent();
		// Click the Sort button and choose Rating
		await page.getByRole('button', { name: 'Sort' }).click();
		await page.getByRole('listbox').waitFor({ state: 'visible', timeout: 5_000 });
		await page.getByRole('listbox').getByText('Rating').click();
		await page.waitForTimeout(1_200);
		const firstAfter = await page.locator('.grid h3').first().textContent();
		// Fellowship has avg_rating 4.5 (highest), should be first after sorting by rating
		expect(firstAfter).not.toBe(firstBefore);
	});

	test('search input syncs with URL query param', async ({ page }) => {
		const searchInput = page.locator('input[placeholder="Search books…"]');
		await searchInput.click();
		await page.waitForTimeout(100);
		await searchInput.pressSequentially('Fellowship', { delay: 50 });
		await page.waitForTimeout(1_500);
		await expect(page).toHaveURL(/\/discover\?q=Fellowship/);
	});

	test('clearing search resets to all 3 books', async ({ page }) => {
		const searchInput = page.locator('input[placeholder="Search books…"]');
		await searchInput.click();
		await page.waitForTimeout(100);
		await searchInput.pressSequentially('Fellowship', { delay: 50 });
		await page.waitForTimeout(1_500);
		await expect(page.locator('.grid h3')).toHaveCount(1);
		// Clear the input with triple-click + Delete
		await searchInput.click({ clickCount: 3 });
		await searchInput.press('Delete');
		await page.waitForTimeout(1_500);
		await expect(page.locator('.grid h3')).toHaveCount(3);
	});
});
