import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { getBook } from '$lib/api/books';
import { fetchUserRating } from '$lib/api/ratings';
import { fetchShelfEntry } from '$lib/api/shelf';

export const load: PageServerLoad = async ({ fetch, params, parent }) => {
	const { user } = await parent();

	const [bookRes, ratingRes, entryRes] = await Promise.all([
		getBook(fetch, params.slug),
		user ? fetchUserRating(fetch, params.slug, true) : Promise.resolve({ data: null, error: null }),
		user ? fetchShelfEntry(fetch, params.slug, true) : Promise.resolve({ data: null, error: null })
	]);

	if (bookRes.error) {
		throw error(bookRes.error.status || 500, bookRes.error.detail);
	}

	return {
		book: bookRes.data!,
		user,
		userRating: ratingRes.data ? { id: ratingRes.data.id, rating: ratingRes.data.rating } : null,
		shelfEntry: entryRes.data ?? null
	};
};
