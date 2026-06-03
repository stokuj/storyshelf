import { test, expect } from './fixtures';

test.describe('Public profile', () => {
	test('public profile shows display_name and handle', async ({ page, guestUser }) => {
		await page.goto(`/u/${guestUser.handle}`);

		// h1 contains the display name (via formatHandleForDisplay)
		await expect(page.getByRole('heading', { level: 1 })).toContainText(guestUser.displayName);

		// Handle shown with @ prefix
		await expect(page.getByText(`@${guestUser.handle}`)).toBeVisible();
	});

	test('owner sees "Edit profile" button on own profile', async ({ page, authUser }) => {
		await page.goto(`/u/${authUser.handle}`);

		await expect(page.getByRole('link', { name: 'Edit profile' })).toBeVisible();
	});

	test('guest does NOT see Follow button on public profile', async ({ page, guestUser }) => {
		// Unauthenticated browser — Follow button must be hidden for guests
		await page.goto(`/u/${guestUser.handle}`);
		await expect(page.getByRole('button', { name: 'Follow' })).toHaveCount(0);
	});

	test('logged-in non-owner sees Follow button', async ({ page, authUser, guestUser }) => {
		// authUser cookies are in the browser context — visiting guestUser's profile
		await page.goto(`/u/${guestUser.handle}`);
		await expect(page.getByRole('button', { name: 'Follow' })).toBeVisible();
	});

	test('nonexistent handle returns 404', async ({ page }) => {
		await page.goto('/u/nonexistent-handle-12345');

		// u/[handle]/+error.svelte renders <h1>Profile not found</h1> for 404
		await expect(page.getByRole('heading', { name: 'Profile not found' })).toBeVisible();
	});

	test('profile with empty bio does not show bio section', async ({ page, guestUser }) => {
		await page.goto(`/u/${guestUser.handle}`);

		// New users have no bio — the bio paragraph should not render.
		// The bio is conditionally rendered: {#if profile.bio}<p class="max-w-lg">...</p>{/if}
		// Check that no element with the CSS class for bio content contains text
		// (the profile header card or other elements could match .max-w-lg)
		const bioElement = page.getByTestId('profile-bio');
		await expect(bioElement).toHaveCount(0);
	});

	test('joined year is displayed', async ({ page, guestUser }) => {
		await page.goto(`/u/${guestUser.handle}`);

		// "Joined" section should be visible in the profile page
		await expect(page.getByText(/Joined/)).toBeVisible();
	});

	test('private profile returns 404 for unauthenticated visitor', async ({ page, privateUser }) => {
		// privateUser has profile_public=False (Django default)
		await page.goto(`/u/${privateUser.handle}`);

		// Should return 404 with "Profile not found" header
		await expect(page.getByRole('heading', { name: 'Profile not found' })).toBeVisible();
	});
});
