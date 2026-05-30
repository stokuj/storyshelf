import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { apiFetch } from '$lib/api/_client';
import type { User } from '$lib/types';

export const load: PageServerLoad = async ({ fetch, params, parent }) => {
	const { data: profile, error: profileErr } = await apiFetch<User>(
		fetch,
		`/u/${params.handle}/`,
		undefined,
		true
	);
	if (profileErr) {
		throw error(profileErr.status === 404 ? 404 : 500, profileErr.detail);
	}

	const { user: viewer } = await parent();
	const isOwner = viewer?.handle === params.handle;

	return { profile, isOwner };
};
