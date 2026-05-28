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

const fellowshipSlug = slugs['The Fellowship of the Ring'];

test.describe('Book detail page', () => {
	test('renders book data: title, author, year, description', async ({ page }) => {
		await page.goto(`/books/${fellowshipSlug}`);
		// Title is in h1 (BookHeader) — appears in both mobile + desktop sections
		await expect(page.getByRole('heading', { level: 1 }).first()).toHaveText(
			'The Fellowship of the Ring'
		);
		// Author link — use .first() since it appears in both mobile and desktop sections
		await expect(page.getByRole('link', { name: 'J.R.R. Tolkien' }).first()).toBeVisible();
		// Year is in BookMeta (desktop layout, hidden on mobile)
		await expect(page.getByText('1954')).toBeVisible();
		// Description contains the expected text — there are two instances (mobile+desktop layout),
		// target the visible one
		await expect(
			page.getByText(/Frodo Baggins inherits the One Ring/).filter({ visible: true })
		).toBeVisible();
	});

	test('shows author name on the detail page', async ({ page }) => {
		await page.goto(`/books/${fellowshipSlug}`);
		// Author appears as a link; use .first() since both layouts render it
		await expect(page.getByRole('link', { name: 'J.R.R. Tolkien' }).first()).toBeVisible();
	});

	test('author name is a link to /discover?author=...', async ({ page }) => {
		await page.goto(`/books/${fellowshipSlug}`);
		const authorLink = page.getByRole('link', { name: 'J.R.R. Tolkien' }).first();
		await expect(authorLink).toBeVisible();
		await authorLink.click();
		await page.waitForURL(/\/discover\?.*author=/);
		await expect(page).toHaveURL(/\/discover\?.*author=/);
	});

	test('cover image renders or fallback title is visible', async ({ page }) => {
		await page.goto(`/books/${fellowshipSlug}`);
		// BookCover renders either <img> or a fallback <span> with the title inside .aspect-[2/3]
		const coverImg = page.locator('img').first();
		const coverFallback = page
			.locator('.aspect-\\[2\\/3\\]')
			.getByText('The Fellowship of the Ring');
		await expect(coverImg.or(coverFallback)).toBeVisible();
	});

	test('404 page for non-existent book slug', async ({ page }) => {
		await page.goto('/books/nieistniejacy-slug-xyz');
		await expect(page.getByText('Book not found')).toBeVisible();
	});

	test('"Browse books" link on 404 page navigates to /discover', async ({ page }) => {
		await page.goto('/books/nieistniejacy-slug-xyz');
		const browseLink = page.getByRole('link', { name: 'Browse books' });
		await expect(browseLink).toBeVisible();
		await browseLink.click();
		await page.waitForURL('/discover');
		await expect(page).toHaveURL('/discover');
	});
});
