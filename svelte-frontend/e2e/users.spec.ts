import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { test, expect } from './fixtures';

const __dirname = dirname(fileURLToPath(import.meta.url));
const slugsPath = resolve(__dirname, '.seed-slugs.json');
let slugs: Record<string, string>;
try {
	slugs = JSON.parse(readFileSync(slugsPath, 'utf-8'));
} catch {
	throw new Error('Missing .seed-slugs.json — run global setup first.');
}
const duneSlug = slugs['Dune'];

test.describe('User discovery', () => {
	test('public user appears in /users, search filters, profile shows Reading', async ({
		page,
		authUser
	}) => {
		// Make the logged-in user public and put a book on their reading shelf.
		const settingsRes = await page.request.patch('/api/users/me/settings/', {
			data: { profile_public: true }
		});
		expect(settingsRes.ok()).toBeTruthy();
		const shelfRes = await page.request.post('/api/shelf/entries/', {
			data: { book_slug: duneSlug, status: 'READING' }
		});
		expect(shelfRes.ok()).toBeTruthy();

		// Discover list: search by handle finds the user.
		await page.goto('/users');
		await page.waitForLoadState('networkidle');
		await page.getByPlaceholder('Search people').fill(authUser.handle);
		await expect(page.getByText(`@${authUser.handle}`)).toBeVisible();

		// Click through to the profile and see the Reading section + the book.
		await page.getByText(`@${authUser.handle}`).click();
		await expect(page.getByRole('heading', { name: 'Reading' })).toBeVisible();
		await expect(page.getByText('Dune')).toBeVisible();
	});

	test('search with no match shows no rows', async ({ page, authUser }) => {
		await page.request.patch('/api/users/me/settings/', { data: { profile_public: true } });
		await page.goto('/users');
		await page.waitForLoadState('networkidle');
		await page.getByPlaceholder('Search people').fill('zzzznomatchzzzz');
		await expect(page.getByText(`@${authUser.handle}`)).toHaveCount(0);
	});
});
