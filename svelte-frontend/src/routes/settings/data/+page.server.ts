import { fail, redirect } from '@sveltejs/kit';
import type { Actions } from './$types';
import { serverApiBase } from '$lib/server/api';

async function apiError(res: Response): Promise<string> {
	const body = await res.json().catch(() => ({}));
	return body.detail ?? body.message ?? `Request failed (${res.status})`;
}

export const actions: Actions = {
	delete: async ({ request, fetch, cookies }) => {
		const data = await request.formData();
		const current_password = data.get('current_password') as string;

		const res = await fetch(`${serverApiBase()}/users/me/`, {
			method: 'DELETE',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ current_password }),
			credentials: 'include'
		});

		if (!res.ok) {
			return fail(res.status, { error: await apiError(res) });
		}

		cookies.delete('access_token', { path: '/' });
		cookies.delete('refresh_token', { path: '/' });
		throw redirect(303, '/');
	}
};
