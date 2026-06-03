import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { getMyStats } from '$lib/api/stats';

export const load: PageServerLoad = async ({ fetch }) => {
	const { data, error: err } = await getMyStats(fetch, true);
	if (err || !data) {
		throw error(err?.status || 500, err?.detail || 'Failed to load stats');
	}
	return { stats: data };
};
