import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { fetchShelfEntries } from '$lib/api/shelf';
import { fetchRatings } from '$lib/api/ratings';
import type { ShelfEntryWithRating } from '$lib/types/shelf';

export const load: PageServerLoad = async ({ fetch }) => {
	const [entriesRes, ratingsRes] = await Promise.all([
		fetchShelfEntries(fetch, true),
		fetchRatings(fetch, true)
	]);

	if (entriesRes.error) {
		throw error(entriesRes.error.status || 500, entriesRes.error.detail || 'Failed to load shelf');
	}

	const ratingIdBySlug = new Map<string, number>();
	for (const r of ratingsRes.data ?? []) ratingIdBySlug.set(r.book_slug, r.id);

	const entries: ShelfEntryWithRating[] = (entriesRes.data ?? []).map((e) => ({
		...e,
		rating_id: ratingIdBySlug.get(e.book.slug) ?? null
	}));

	return { entries };
};
