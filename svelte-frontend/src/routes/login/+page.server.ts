import { fail, redirect } from '@sveltejs/kit';
import type { Actions } from './$types';
import { serverApiBase } from '$lib/server/api';
import { forwardSetCookies } from '$lib/server/cookies';

export const actions: Actions = {
	default: async ({ request, fetch, cookies, url }) => {
		const formData = await request.formData();
		const email = formData.get('email') as string;
		const password = formData.get('password') as string;

		if (!email || !password) {
			return fail(400, { email, missing: !email ? 'email' : 'password' });
		}

		const res = await fetch(`${serverApiBase()}/auth/login/`, {
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

		// Honor ?next= from auth guards, but only same-origin relative paths
		// (a leading single slash) to avoid open-redirect.
		const next = url.searchParams.get('next');
		const target = next && next.startsWith('/') && !next.startsWith('//') ? next : '/discover';
		throw redirect(303, target);
	}
};
