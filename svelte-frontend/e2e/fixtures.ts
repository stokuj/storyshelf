import { test as base, type APIRequestContext, type Cookie } from '@playwright/test';
import { randomUUID } from 'node:crypto';

// ── Constants ─────────────────────────────────────────────────────────

export const API_BASE_URL = process.env.TEST_API_URL ?? 'http://localhost:8000';

/** Test password used for all registered users. Centralized so it's easy to change. */
export const TEST_PASSWORD = 'TestPass123!';

// ── Types ────────────────────────────────────────────────────────────

export interface AuthUser {
	email: string;
	password: string;
	displayName: string;
	handle: string;
}

// ── Helpers ──────────────────────────────────────────────────────────

export function uniqueEmail(): string {
	return `test-${randomUUID().slice(0, 8)}@e2e.example`;
}

function uniqueDisplayName(): string {
	return `Test ${randomUUID().slice(0, 6)}`;
}

function uniqueHandle(): string {
	// Django requires handle to match ^[a-z]{3,30}$ (lowercase letters only).
	const letters = (randomUUID() + randomUUID()).replace(/[^a-f]/g, '');
	return `t${letters}`.slice(0, 30);
}

/**
 * Remove the HTML `required` attribute from an input so the browser doesn't
 * block form submission before server-side validation runs.
 */
export async function bypassRequired(locator: import('@playwright/test').Locator): Promise<void> {
	await locator.evaluate((el) => el.removeAttribute('required'));
}

/**
 * Register a new user via the Django API. Returns user info and auth cookies.
 * Cookies come from api.storageState() — avoids hand-rolled Set-Cookie parsing.
 * Django endpoint: POST /api/auth/register/ with { email, handle, display_name, password }
 */
async function registerUser(api: APIRequestContext): Promise<{
	user: AuthUser;
	cookies: Cookie[];
}> {
	const email = uniqueEmail();
	const password = TEST_PASSWORD;
	const displayName = uniqueDisplayName();
	const handle = uniqueHandle();

	const res = await api.post('/api/auth/register/', {
		data: { email, display_name: displayName, password, handle }
	});

	if (!res.ok()) {
		throw new Error(`Registration failed: ${res.status()} ${await res.text()}`);
	}

	const data = await res.json();
	const { cookies } = await api.storageState();

	return {
		user: { email, password, displayName, handle: data.handle },
		cookies
	};
}

/**
 * Delete the currently authenticated user via the API.
 * Django's AccountDeleteSerializer requires current_password in the request body.
 * Checks response status — .catch() alone misses 401/403 since they're not network errors.
 */
export async function deleteUser(api: APIRequestContext, password: string): Promise<void> {
	const res = await api.delete('/api/users/me/', {
		data: { current_password: password }
	});
	if (!res.ok()) {
		const body = await res.text();
		throw new Error(`[fixture] User cleanup failed: ${res.status()} ${body}`);
	}
}

/**
 * Delete a user via the API using saved registration cookies.
 * Used by fixture teardown. Creates a new APIRequestContext for the deletion.
 */
async function teardownUserViaApi(
	playwright: import('@playwright/test').PlaywrightTestArgs['playwright'],
	cookies: Cookie[],
	password: string
): Promise<void> {
	const authedApi = await playwright.request.newContext({
		baseURL: API_BASE_URL,
		storageState: { cookies }
	});
	await deleteUser(authedApi, password);
	await authedApi.dispose();
}

// ── Fixtures ─────────────────────────────────────────────────────────

type Fixtures = {
	/** Django API request context (baseURL: http://localhost:8000) */
	api: APIRequestContext;
	/** Fresh registered user with auth cookies in browser context. Auto-deleted after test. */
	authUser: AuthUser;
	/** Fresh registered user without browser cookies (for visibility tests). Auto-deleted after test. */
	guestUser: AuthUser;
	/** Fresh registered user with profile_public=False (default). No browser cookies. Auto-deleted after test. */
	privateUser: AuthUser;
};

export const test = base.extend<Fixtures>({
	// API context pointing to Django backend
	api: async ({ playwright }, use) => {
		const api = await playwright.request.newContext({ baseURL: API_BASE_URL });
		await use(api);
		await api.dispose();
	},

	// Authenticated user: registers via API, injects cookies into context, tears down via API
	authUser: async ({ api, context, playwright }, use) => {
		const { user, cookies } = await registerUser(api);

		// Inject cookies into the browser context
		await context.addCookies(cookies);

		await use(user);

		// Teardown: prefer browser's current cookies (includes refreshed tokens from
		// password changes). Fall back to registration cookies if browser cookies are
		// empty (e.g. test called clearCookies()) or the cleanup fails with 401/403.
		// PasswordChangeView blacklists all outstanding tokens, so registration
		// cookies may be invalid if the test changed the password.
		const browserCookies = await context.cookies();
		const hasAuthCookies = browserCookies.some(
			(c) => c.name === 'access_token' || c.name === 'refresh_token'
		);

		try {
			if (hasAuthCookies) {
				await teardownUserViaApi(playwright, browserCookies, user.password);
				return;
			}
		} catch (err) {
			console.warn(
				'[fixture] authUser teardown: browser cookies failed, using fallback registration cookies:',
				err
			);
		}

		// Fallback: try registration cookies (works if password wasn't changed)
		await teardownUserViaApi(playwright, cookies, user.password);
	},

	// Guest user: registered but no browser cookies (for testing public visibility)
	guestUser: async ({ api, playwright }, use) => {
		const { user, cookies } = await registerUser(api);

		// Make profile public so unauthenticated visitors can see it
		// (Django default: profile_public=False — profiles are private)
		const authedSetup = await playwright.request.newContext({
			baseURL: API_BASE_URL,
			storageState: { cookies }
		});
		const res = await authedSetup.patch('/api/users/me/settings/', {
			data: { profile_public: true }
		});
		if (!res.ok()) {
			throw new Error(
				`[fixture] guestUser: failed to make profile public (PATCH /api/users/me/settings/). ` +
					`Status: ${res.status()}. Profile tests will produce false negatives.`
			);
		}
		await authedSetup.dispose();

		await use(user);

		// Teardown: reuse registration cookies to delete user (no login needed)
		await teardownUserViaApi(playwright, cookies, user.password);
	},

	// Private user: registered but no browser cookies, profile_public remains False (Django default)
	privateUser: async ({ api, playwright }, use) => {
		const { user, cookies } = await registerUser(api);

		// DO NOT PATCH profile_public — leave as False (default)
		// This user's profile should return 404 for unauthenticated visitors

		await use(user);

		// Teardown: reuse registration cookies to delete user
		await teardownUserViaApi(playwright, cookies, user.password);
	}
});

export { expect } from '@playwright/test';
