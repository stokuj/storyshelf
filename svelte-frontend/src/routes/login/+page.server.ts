import { fail, redirect } from '@sveltejs/kit';
import type { Actions } from './$types';
import { PUBLIC_API_URL } from '$lib/config';
import { forwardSetCookies } from '$lib/server/cookies';

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

		if (!res.ok) {
			const err = await res.json().catch(() => ({}));
			return fail(400, { email, error: err.detail ?? err.message ?? 'Invalid credentials' });
		}

		forwardSetCookies(res, cookies);

		throw redirect(303, '/discover');
	}
};
