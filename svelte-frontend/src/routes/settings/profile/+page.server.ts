import { fail } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import { serverApiBase } from '$lib/server/api';

export const load: PageServerLoad = async ({ fetch }) => {
	const res = await fetch(`${serverApiBase()}/users/me/settings/`, {
		credentials: 'include'
	});
	const settings = res.ok ? await res.json() : { profile_public: true };
	return { profilePublic: settings.profile_public as boolean };
};

export const actions: Actions = {
	privacy: async ({ request, fetch }) => {
		const data = await request.formData();
		const profilePublic = data.get('profile_public') === 'on';
		const res = await fetch(`${serverApiBase()}/users/me/settings/`, {
			method: 'PATCH',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ profile_public: profilePublic }),
			credentials: 'include'
		});
		if (!res.ok) {
			const body = await res.json().catch(() => ({}));
			return fail(res.status, { error: body.detail ?? `Request failed (${res.status})` });
		}
		return { success: true };
	}
};
