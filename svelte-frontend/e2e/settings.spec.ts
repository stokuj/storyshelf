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

		// Data & export
		await page.getByRole('link', { name: 'Data & export' }).click();
		await page.waitForURL('**/settings/data');
		await expect(page.getByRole('heading', { name: 'Export your data' })).toBeVisible();
	});

	test('delete account dialog rejects a wrong password', async ({ page, authUser }) => {
		await page.goto('/settings/data');
		await expect(page.getByRole('heading', { name: 'Export your data' })).toBeVisible();
		await expect(page.getByRole('heading', { name: 'Danger zone' })).toBeVisible();

		// The dialog opens via a client onclick, so retry the trigger click until the
		// page has hydrated and the password field appears (avoids a pre-hydration race).
		await expect(async () => {
			await page.getByRole('button', { name: 'Delete account' }).click();
			await expect(page.getByPlaceholder('Your password')).toBeVisible({ timeout: 1000 });
		}).toPass();

		await page.getByPlaceholder('Your password').fill('definitely-wrong-password');
		await page.getByRole('button', { name: 'Delete my account' }).click();

		// Backend returns 403 → action returns fail(), so we stay on /settings/data.
		await expect(page).toHaveURL(/\/settings\/data/);
	});

	test('export data triggers a zip download', async ({ page, authUser }) => {
		await page.goto('/settings/data');
		const downloadPromise = page.waitForEvent('download');
		await page.getByRole('link', { name: 'Export all data' }).click();
		const download = await downloadPromise;
		expect(download.suggestedFilename()).toMatch(/\.zip$/);
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
