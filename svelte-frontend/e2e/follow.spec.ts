import { type Page } from '@playwright/test';
import { test, expect } from './fixtures';

// Wait for Svelte to hydrate before interacting with client-side buttons.
// Same pattern used in shelf-status.spec.ts to avoid clicking server-rendered
// buttons before their onclick handlers are attached.
async function gotoReady(page: Page, url: string) {
	await page.goto(url);
	await page.waitForLoadState('networkidle');
}

test.describe('Follow flow', () => {
	test('follow increments count and shows up in followers list; unfollow reverts', async ({
		page,
		authUser,
		guestUser
	}) => {
		// authUser is the logged-in browser; guestUser is a public profile to follow.
		await gotoReady(page, `/u/${guestUser.handle}`);

		// Guard: if a prior aborted run left a follow relationship, unfollow first.
		const unfollowBtn = page.getByRole('button', { name: 'Unfollow' });
		if (await unfollowBtn.isVisible()) {
			await Promise.all([
				page.waitForResponse((r) => r.url().includes('/follow/') && r.status() === 204),
				unfollowBtn.click()
			]);
			await expect(page.getByRole('button', { name: 'Follow' })).toBeVisible();
		}

		const followBtn = page.getByRole('button', { name: 'Follow' });
		await expect(followBtn).toBeVisible();

		// Wait for the actual API response (not just the optimistic UI update).
		await Promise.all([
			page.waitForResponse((r) => r.url().includes('/follow/') && r.status() === 201),
			followBtn.click()
		]);
		await expect(page.getByRole('button', { name: 'Unfollow' })).toBeVisible();

		// Followers list shows the logged-in user.
		await gotoReady(page, `/u/${guestUser.handle}/followers`);
		await expect(page.getByText(`@${authUser.handle}`)).toBeVisible();

		// Unfollow from the profile.
		await gotoReady(page, `/u/${guestUser.handle}`);
		await Promise.all([
			page.waitForResponse((r) => r.url().includes('/follow/') && r.status() === 204),
			page.getByRole('button', { name: 'Unfollow' }).click()
		]);
		await expect(page.getByRole('button', { name: 'Follow' })).toBeVisible();

		// Followers list no longer shows the user.
		await gotoReady(page, `/u/${guestUser.handle}/followers`);
		await expect(page.getByText(`@${authUser.handle}`)).toHaveCount(0);
	});
});
