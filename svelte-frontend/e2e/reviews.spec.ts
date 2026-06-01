// Reviews (M4) E2E. Requires the dev stack up (Django :8000 + seeded books) and the
// Vite `/api` proxy (ADR-002). Relax the register throttle on the server with
// `THROTTLE_AUTH_REGISTER=1000/min`. Run with `npm run test:e2e`. Not part of CI.
import { type Cookie, type Page } from '@playwright/test';
import { test, expect } from './fixtures';
import { cleanupMyReview } from './helpers/seed';

const BOOK = { slug: 'the-hobbit', title: 'The Hobbit' } as const;

async function gotoReady(page: Page, url: string) {
	await page.goto(url);
	await page.waitForLoadState('networkidle');
}

test.describe('Reviews', () => {
	test('logged-in user posts a review and it appears in the list', async ({
		page,
		authUser,
		playwright
	}) => {
		await gotoReady(page, `/books/${BOOK.slug}`);
		await page.getByTestId('review-textarea').fill('A wonderful adventure.');
		await page.getByRole('button', { name: /post review/i }).click();

		await expect(page.getByTestId('review-card')).toContainText('A wonderful adventure.');

		await cleanupMyReview(BOOK.slug, await page.context().cookies(), playwright);
	});

	test('user edits their review', async ({ page, authUser, playwright }) => {
		await gotoReady(page, `/books/${BOOK.slug}`);
		await page.getByTestId('review-textarea').fill('First take.');
		await page.getByRole('button', { name: /post review/i }).click();
		await expect(page.getByTestId('review-card')).toContainText('First take.');

		await page.getByTestId('review-textarea').fill('Revised take.');
		await page.getByRole('button', { name: /update review/i }).click();
		await expect(page.getByTestId('review-card')).toContainText('Revised take.');
		await expect(page.getByTestId('review-card')).toHaveCount(1);

		await cleanupMyReview(BOOK.slug, await page.context().cookies(), playwright);
	});

	test('user deletes their review', async ({ page, authUser }) => {
		await gotoReady(page, `/books/${BOOK.slug}`);
		await page.getByTestId('review-textarea').fill('To be deleted.');
		await page.getByRole('button', { name: /post review/i }).click();
		await expect(page.getByTestId('review-card')).toHaveCount(1);

		await page.getByRole('button', { name: /delete/i }).click();
		await expect(page.getByTestId('review-card')).toHaveCount(0);
		await expect(page.getByTestId('reviews-empty')).toBeVisible();
	});

	test('anonymous user sees the list but no form', async ({ page, authUser, playwright }) => {
		// Seed a review as the authenticated user, then drop to anonymous.
		await gotoReady(page, `/books/${BOOK.slug}`);
		await page.getByTestId('review-textarea').fill('Visible to all.');
		await page.getByRole('button', { name: /post review/i }).click();
		await expect(page.getByTestId('review-card')).toContainText('Visible to all.');

		const cookies = await page.context().cookies();
		await page.context().clearCookies();
		await gotoReady(page, `/books/${BOOK.slug}`);

		await expect(page.getByTestId('review-card')).toContainText('Visible to all.');
		await expect(page.getByTestId('review-form')).toHaveCount(0);

		await cleanupMyReview(BOOK.slug, cookies as Cookie[], playwright);
	});
});
