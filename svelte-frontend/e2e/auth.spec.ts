import {
	test,
	expect,
	deleteUser,
	API_BASE_URL,
	TEST_PASSWORD,
	bypassRequired,
	uniqueEmail
} from './fixtures';

test.describe('Authentication', () => {
	test('signup with valid data redirects to home', async ({ page, playwright }) => {
		await page.goto('/signup');

		const email = uniqueEmail();
		await page.fill('#email', email);
		await page.fill('#display_name', 'Signup Test');
		await page.fill('#password', TEST_PASSWORD);
		await page.click('button[type="submit"]');

		await page.waitForURL('/');
		await expect(page).toHaveURL('/');

		// Cleanup: delete the registered user via authenticated API
		const cookies = await page.context().cookies();
		const authedApi = await playwright.request.newContext({
			baseURL: API_BASE_URL,
			storageState: { cookies }
		});
		await deleteUser(authedApi, TEST_PASSWORD);
		await authedApi.dispose();
	});

	test('signup with empty display_name shows error', async ({ page }) => {
		await page.goto('/signup');

		await page.fill('#email', uniqueEmail());
		await bypassRequired(page.locator('#display_name'));
		await page.fill('#display_name', '');
		await page.fill('#password', TEST_PASSWORD);
		await page.click('button[type="submit"]');

		await expect(page.getByText('Display name is required')).toBeVisible();
	});

	test('signup with short password shows error', async ({ page }) => {
		await page.goto('/signup');

		await page.fill('#email', uniqueEmail());
		await page.fill('#display_name', 'Short PW');
		await page.fill('#password', '12345');
		await page.click('button[type="submit"]');

		await expect(page.getByText('Password must be at least 8 characters')).toBeVisible();
	});

	test('signup with empty email shows error', async ({ page }) => {
		await page.goto('/signup');

		await bypassRequired(page.locator('#email'));
		await page.fill('#email', '');
		await page.fill('#display_name', 'No Email');
		await page.fill('#password', TEST_PASSWORD);
		await page.click('button[type="submit"]');

		await expect(page.getByText('Email is required')).toBeVisible();
	});

	test('login with valid credentials redirects to home', async ({ page, guestUser }) => {
		await page.goto('/login');

		await page.fill('#email', guestUser.email);
		await page.fill('#password', guestUser.password);
		await page.click('button[type="submit"]');

		await page.waitForURL('/');
		await expect(page).toHaveURL('/');

		// Verify logged in — nav shows avatar, not "Sign in"
		await expect(page.getByRole('button', { name: 'Open user menu' })).toBeVisible();
	});

	test('login with wrong password shows error', async ({ page }) => {
		await page.goto('/login');

		await page.fill('#email', 'nobody@example.com');
		await page.fill('#password', 'wrong-password');
		await page.click('button[type="submit"]');

		await expect(page.getByRole('alert')).toBeVisible();
	});

	test('login with empty email shows error', async ({ page }) => {
		await page.goto('/login');

		await bypassRequired(page.locator('#email'));
		await page.fill('#email', '');
		await page.fill('#password', 'anything');
		await page.click('button[type="submit"]');

		await expect(page).toHaveURL(/\/login/);
	});

	test('login with empty password shows error', async ({ page }) => {
		await page.goto('/login');

		await page.fill('#email', 'someone@example.com');
		await bypassRequired(page.locator('#password'));
		await page.fill('#password', '');
		await page.click('button[type="submit"]');

		await expect(page).toHaveURL(/\/login/);
	});

	test('logout clears auth and redirects to login', async ({ page, authUser }) => {
		// Already logged in via authUser fixture
		await page.goto('/');

		// Verify logged in — nav shows avatar
		await expect(page.getByRole('button', { name: 'Open user menu' })).toBeVisible();

		// Clear cookies to simulate logout (avoids dropdown portal interaction issues)
		await page.context().clearCookies();

		// Navigate to protected page — should redirect to login since auth gone
		await page.goto('/settings');
		await page.waitForURL(/\/login/);
		await expect(page).toHaveURL(/\/login/);
	});

	test('sign out via UI button redirects to login', async ({ page, authUser }) => {
		// Already logged in via authUser fixture
		await page.goto('/logout');

		// The /logout page renders a form with a "Sign out" button (SvelteKit fallback)
		await page.getByRole('button', { name: 'Sign out' }).click();

		// After POST /logout, SvelteKit redirects to /login
		await page.waitForURL('/login');
		await expect(page).toHaveURL('/login');

		// Verify logged out — "Sign in" link should be visible in nav
		await expect(page.getByRole('link', { name: 'Sign in' })).toBeVisible();
	});

	test('unauthenticated user visiting /settings is redirected to /login', async ({ page }) => {
		await page.goto('/settings');
		await page.waitForURL('**/login**');
		await expect(page).toHaveURL(/\/login/);
	});

	test('logged-in user visiting /login is redirected to home', async ({ page, authUser }) => {
		await page.goto('/login');
		await page.waitForURL('/');
		await expect(page).toHaveURL('/');
	});

	test('logged-in user visiting /signup is redirected to home', async ({ page, authUser }) => {
		await page.goto('/signup');
		await page.waitForURL('/');
		await expect(page).toHaveURL('/');
	});
});
