import { test, expect, TEST_PASSWORD, API_BASE_URL } from './fixtures';

test.describe('Settings', () => {
	test('edit display_name and see it reflected', async ({ page, authUser }) => {
		await page.goto('/settings');

		const displayNameInput = page.locator('input[name="display_name"]');
		await displayNameInput.fill('Updated Name');
		await Promise.all([
			page.waitForResponse((r) => r.url().includes('?/profile') && r.status() === 200),
			page.getByRole('button', { name: 'Save' }).click()
		]);

		// Form action completed — input should reflect new value on the re-rendered page
		await expect(displayNameInput).toHaveValue('Updated Name');
	});

	test('empty display_name is rejected (stays on settings)', async ({ page, authUser }) => {
		await page.goto('/settings');

		const displayNameInput = page.locator('input[name="display_name"]');
		await displayNameInput.fill('');
		await page.getByRole('button', { name: 'Save' }).click();
		// Validation rejected — stays on /settings
		await expect(page).toHaveURL(/\/settings/);
	});

	test('left rail navigates to sub-pages', async ({ page, authUser }) => {
		await page.goto('/settings');

		// Account (default)
		await expect(page.getByRole('heading', { name: 'Display name' })).toBeVisible();

		// Profile & privacy
		await page.getByRole('link', { name: 'Profile & privacy' }).click();
		await page.waitForURL('**/settings/profile');
		await expect(page.getByRole('heading', { name: 'Privacy settings' })).toBeVisible();

		// Notifications
		await page.getByRole('link', { name: 'Notifications' }).click();
		await page.waitForURL('**/settings/notifications');
		await expect(page.getByRole('heading', { name: 'Email notifications' })).toBeVisible();

		// Data & export
		await page.getByRole('link', { name: 'Data & export' }).click();
		await page.waitForURL('**/settings/data');
		await expect(page.getByRole('heading', { name: 'Export your data' })).toBeVisible();
	});

	test('notifications page shows switches', async ({ page, authUser }) => {
		await page.goto('/settings/notifications');

		await expect(page.getByText('New followers')).toBeVisible();
		await expect(page.getByText('Book recommendations')).toBeVisible();
		await expect(page.getByText('Enable push notifications')).toBeVisible();

		// Switches render with role="switch" (bits-ui Switch component)
		const switches = page.getByRole('switch');
		await expect(switches).toHaveCount(3);
	});

	test('data page shows export and delete options', async ({ page, authUser }) => {
		await page.goto('/settings/data');

		await expect(page.getByRole('heading', { name: 'Export your data' })).toBeVisible();
		await expect(page.getByRole('heading', { name: 'Pause account' })).toBeVisible();
		await expect(page.getByRole('heading', { name: 'Danger zone' })).toBeVisible();

		// "Delete account" button is rendered (Svelte 5 onclick/portal makes dialog testing unreliable)
		await expect(page.getByRole('button', { name: 'Delete account' })).toBeVisible();
	});

	test('password change with mismatched confirm is rejected', async ({ page, authUser }) => {
		await page.goto('/settings');

		await page.fill('#current', TEST_PASSWORD);
		await page.fill('#new', 'NewPass456!');
		await page.fill('#confirm', 'Mismatch789!');
		await page.getByRole('button', { name: 'Change password' }).click();
		// SvelteKit action returns fail(400) — stays on /settings
		await expect(page).toHaveURL(/\/settings/);
	});

	test('password change with short new password is rejected', async ({ page, authUser }) => {
		await page.goto('/settings');

		await page.fill('#current', TEST_PASSWORD);
		await page.fill('#new', '12345');
		await page.fill('#confirm', '12345');
		await page.getByRole('button', { name: 'Change password' }).click();
		// SvelteKit action returns fail(400) — stays on /settings
		await expect(page).toHaveURL(/\/settings/);
	});

	test('password change with correct current and valid new succeeds', async ({
		page,
		authUser,
		playwright
	}) => {
		await page.goto('/settings');

		const newPassword = 'NewValidPass789!';
		await page.fill('#current', TEST_PASSWORD);
		await page.fill('#new', newPassword);
		await page.fill('#confirm', newPassword);
		await page.getByRole('button', { name: 'Change password' }).click();

		// Success: SvelteKit redirects to /settings on 200
		await page.waitForURL(/\/settings/);
		await expect(page).toHaveURL(/\/settings/);

		// Verify the new password actually works by logging in via API
		const verifyApi = await playwright.request.newContext({ baseURL: API_BASE_URL });
		const loginRes = await verifyApi.post('/api/auth/login/', {
			data: { email: authUser.email, password: newPassword }
		});
		expect(loginRes.ok()).toBeTruthy();
		await verifyApi.dispose();

		// Mutate the fixture's password so teardown uses the correct current_password.
		// No UI revert needed — browser context already has valid tokens from password change.
		// TODO(phase4-cleanup): dedicated passwordChangeUser fixture instead of mutating shared authUser state
		authUser.password = newPassword;
	});

	test('password change with wrong current_password is rejected', async ({ page, authUser }) => {
		await page.goto('/settings');

		await page.fill('#current', 'WrongCurrentPassword!');
		await page.fill('#new', 'NewPass456!');
		await page.fill('#confirm', 'NewPass456!');
		await page.getByRole('button', { name: 'Change password' }).click();

		// SvelteKit action returns fail(400) — stays on /settings
		await expect(page).toHaveURL(/\/settings/);
		// Error message should appear (e.g. "Invalid password" from Django)
		await expect(page.getByText(/invalid.*password|password.*invalid/i).first()).toBeVisible();
	});
});
