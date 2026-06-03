// Custom shelves (M5) E2E. Requires the dev stack up (Django :8000 + seeded books)
// and the Vite `/api` proxy (ADR-002). Relax the register throttle on the server
// with `THROTTLE_AUTH_REGISTER=1000/min`. Run with `npm run test:e2e`. Not part of CI.
import { type Cookie, type Page } from '@playwright/test';
import { test, expect, API_BASE_URL } from './fixtures';
import { seedShelf, cleanupShelves } from './helpers/seed';

const BOOK = { slug: 'the-fellowship-of-the-ring', title: 'The Fellowship of the Ring' } as const;

// Navigate and wait for the client bundle to settle so Svelte has hydrated and
// click handlers are attached before we interact.
async function gotoReady(page: Page, url: string) {
	await page.goto(url);
	await page.waitForLoadState('networkidle');
}

// Make the current browser user's profile public via API (Django default is private,
// which would otherwise hide all shelves from guests).
async function makeProfilePublic(
	cookies: Cookie[],
	playwright: typeof import('@playwright/test').playwright
) {
	const api = await playwright.request.newContext({
		baseURL: API_BASE_URL,
		storageState: { cookies, origins: [] }
	});
	const res = await api.patch('/api/users/me/settings/', { data: { profile_public: true } });
	expect(res.ok()).toBe(true);
	await api.dispose();
}

test.describe('Custom shelves', () => {
	test('create a shelf, add a book from book detail, shelf shows 1 book', async ({
		page,
		authUser,
		playwright
	}) => {
		// Create the shelf from the "My shelves" tab. Retry the submit until the shelf
		// appears — in dev a click can land before Svelte hydration attaches the handler.
		await gotoReady(page, '/shelf');
		await page.getByTestId('shelf-view-tab').filter({ hasText: 'My shelves' }).click();
		await page.getByTestId('shelf-name-input').fill('Summer reads');
		await expect(async () => {
			await page.getByTestId('shelf-create-submit').click();
			await expect(page.getByTestId('shelf-card')).toContainText('Summer reads', {
				timeout: 1000
			});
		}).toPass();
		await expect(page.getByTestId('shelf-card')).toContainText('0 books');

		// Add a seeded book to it from the book detail page (native <details> dropdown).
		// Open the dropdown (retry to dodge the dev hydration race), then toggle the
		// checkbox exactly once and wait for the membership POST so we don't double-toggle.
		await gotoReady(page, `/books/${BOOK.slug}`);
		const dropdown = page.getByTestId('add-to-shelf-dropdown');
		const checkbox = dropdown.getByRole('checkbox');
		await expect(async () => {
			await dropdown.getByText('Add to shelf').click();
			await expect(checkbox).toBeVisible({ timeout: 1000 });
		}).toPass();
		const addResponse = page.waitForResponse(
			(r) => r.url().includes('/shelves/summer-reads/books/') && r.request().method() === 'POST'
		);
		await checkbox.click();
		await addResponse;
		await expect(checkbox).toBeChecked();

		// Verify the shelf now contains the book (detail page reads fresh from the API).
		await gotoReady(page, '/shelf/summer-reads');
		await expect(page.getByTestId('shelf-book')).toHaveCount(1);
		await expect(page.getByTestId('shelf-book')).toContainText(BOOK.title);
		await expect(page.getByText('1 books')).toBeVisible();

		await cleanupShelves(await page.context().cookies(), playwright);
	});

	test('public shelf with a book is visible to a guest', async ({ page, authUser, playwright }) => {
		const cookies = await page.context().cookies();
		await makeProfilePublic(cookies, playwright);
		const shelf = await seedShelf(
			{ name: 'Public picks', is_public: true, book_slugs: [BOOK.slug] },
			cookies,
			playwright
		);

		// Guest context: drop the auth cookies and visit the public shelf URL.
		await page.context().clearCookies();
		await gotoReady(page, `/u/${authUser.handle}/shelves/${shelf.slug}`);

		await expect(page.getByRole('heading', { name: 'Public picks' })).toBeVisible();
		await expect(page.getByText(BOOK.title).first()).toBeVisible();

		await cleanupShelves(cookies, playwright);
	});

	test('private shelf returns 404 for a guest', async ({ page, authUser, playwright }) => {
		const cookies = await page.context().cookies();
		// Profile stays private (Django default) and the shelf is private too.
		const shelf = await seedShelf(
			{ name: 'Secret stash', is_public: false, book_slugs: [BOOK.slug] },
			cookies,
			playwright
		);

		await page.context().clearCookies();
		const res = await page.goto(`/u/${authUser.handle}/shelves/${shelf.slug}`);
		expect(res?.status()).toBe(404);
		await expect(page.getByText('Secret stash')).toHaveCount(0);

		await cleanupShelves(cookies, playwright);
	});

	test('delete a shelf from its detail page removes it from the list', async ({
		page,
		authUser,
		playwright
	}) => {
		const cookies = await page.context().cookies();
		const shelf = await seedShelf({ name: 'To delete' }, cookies, playwright);

		await gotoReady(page, `/shelf/${shelf.slug}`);
		page.on('dialog', (d) => d.accept());
		await page.getByTestId('shelf-delete').click();

		// Deletion navigates back to /shelf. Open "My shelves" and confirm it's gone.
		await expect(page).toHaveURL(/\/shelf$/);
		await page.getByTestId('shelf-view-tab').filter({ hasText: 'My shelves' }).click();
		await expect(page.getByText('To delete')).toHaveCount(0);

		await cleanupShelves(cookies, playwright);
	});
});
