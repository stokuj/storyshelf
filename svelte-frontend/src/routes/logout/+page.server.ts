import { redirect } from '@sveltejs/kit';
import type { Actions } from './$types';
import { PUBLIC_API_URL } from '$lib/config';

export const actions: Actions = {
	default: async ({ fetch, cookies }) => {
		// Best-effort: tell backend to invalidate the session.
		await fetch(`${PUBLIC_API_URL}/auth/logout/`, {
			method: 'POST',
			credentials: 'include'
		}).catch(() => {});

		// Always clear auth cookies regardless of backend response.
		cookies.delete('access_token', { path: '/' });
		cookies.delete('refresh_token', { path: '/' });

		throw redirect(303, '/');
	}
};
