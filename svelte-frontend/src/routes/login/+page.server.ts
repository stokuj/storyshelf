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

		// Copy Set-Cookie headers from API response to our response
		const setCookie = res.headers.get('set-cookie');
		if (setCookie) {
			cookies.set('storyshelf_session', setCookie, {
				path: '/',
				httpOnly: true,
				secure: false,
				sameSite: 'lax'
			});
		}

		if (!res.ok) {
			const err = await res.json().catch(() => ({}));
			return fail(400, { email, error: err.detail ?? err.message ?? 'Invalid credentials' });
		}

		throw redirect(303, '/discover');
	}
};
