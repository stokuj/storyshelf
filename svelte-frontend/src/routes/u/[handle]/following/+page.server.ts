import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { fetchFollowing } from '$lib/api/follow';

export const load: PageServerLoad = async ({ fetch, params }) => {
	const { data, error: err } = await fetchFollowing(fetch, params.handle, true);
	if (err) {
		throw error(err.status === 404 ? 404 : 500, err.detail);
	}
	return { handle: params.handle, users: data ?? [] };
};
