import { fail, redirect } from '@sveltejs/kit';
import type { Actions } from './$types';
import { PUBLIC_API_URL } from '$lib/config';

export const actions: Actions = {
	default: async ({ request, fetch, cookies }) => {
		const formData = await request.formData();
		const email = formData.get('email') as string;
		const handle = formData.get('handle') as string;
		const password = formData.get('password') as string;

		const errors: Record<string, string> = {};
		if (!email) errors.email = 'Email is required';
		if (!handle || handle.length < 3) errors.handle = 'Handle must be at least 3 characters';
		if (!password || password.length < 8)
			errors.password = 'Password must be at least 8 characters';

		if (Object.keys(errors).length > 0) {
			return fail(400, { email, handle, errors });
		}

		const res = await fetch(`${PUBLIC_API_URL}/auth/register/`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ email, handle, password, display_name: handle }),
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
			return fail(400, {
				email,
				handle,
				error: err.detail ?? err.message ?? 'Registration failed'
			});
		}

		throw redirect(303, '/discover');
	}
};
