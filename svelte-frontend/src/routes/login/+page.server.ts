import { fail, redirect } from '@sveltejs/kit';
import type { Actions } from './$types';
import { PUBLIC_API_URL } from '$lib/config';

export const actions: Actions = {
	default: async ({ request, fetch, cookies }) => {
		const formData = await request.formData();
		const email = formData.get('email') as string;
		const password = formData.get('password') as string;

		if (!email || !password) {
			return fail(400, { email, missing: !email ? 'email' : 'password' });
		}

		const res = await fetch(`${PUBLIC_API_URL}/auth/login/`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ email, password }),
			credentials: 'include'
		});

		// Forward all Set-Cookie headers from the API response to the browser.
		// The backend uses 'access_token' and 'refresh_token' cookie names (see backend-django/users/cookie_auth.py).
		for (const cookieStr of res.headers.getSetCookie()) {
			const eq = cookieStr.indexOf('=');
			if (eq > 0) {
				const name = cookieStr.slice(0, eq);
				const value = cookieStr.slice(
					eq + 1,
					cookieStr.indexOf(';') > 0 ? cookieStr.indexOf(';') : undefined
				);
				cookies.set(name, value, {
					path: '/',
					httpOnly: true,
					secure: false,
					sameSite: 'lax'
				});
			}
		}

		if (!res.ok) {
			const err = await res.json().catch(() => ({}));
			return fail(400, { email, error: err.detail ?? err.message ?? 'Invalid credentials' });
		}

		throw redirect(303, '/discover');
	}
};
