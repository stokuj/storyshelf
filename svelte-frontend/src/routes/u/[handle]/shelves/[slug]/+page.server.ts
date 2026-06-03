import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { fetchPublicShelf } from '$lib/api/shelves';

export const load: PageServerLoad = async ({ fetch, params }) => {
	const { data, error: err } = await fetchPublicShelf(fetch, params.handle, params.slug, true);
	if (err) {
		throw error(err.status === 404 ? 404 : 500, err.detail || 'Failed to load shelf');
	}
	return { shelf: data!, handle: params.handle };
};
