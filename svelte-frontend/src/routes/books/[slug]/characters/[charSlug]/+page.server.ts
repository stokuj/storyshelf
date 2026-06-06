import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { fetchCharacter } from '$lib/api/characters';

export const load: PageServerLoad = async ({ fetch, params }) => {
	const { data, error: err } = await fetchCharacter(fetch, params.slug, params.charSlug, true);
	if (err || !data) {
		throw error(err?.status || 404, err?.detail || 'Character not found');
	}
	return { character: data, bookSlug: params.slug };
};
