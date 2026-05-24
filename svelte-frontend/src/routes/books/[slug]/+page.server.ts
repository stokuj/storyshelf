import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { getBook, getReviews } from '$lib/api/books';
import { getExtraction } from '$lib/api/ai';
import { getShelfEntry, type ShelfStatus } from '$lib/api/shelves';

export const load: PageServerLoad = async ({ fetch, params, parent }) => {
	const [{ user }, bookRes, reviewsRes] = await Promise.all([
		parent(),
		getBook(fetch, params.slug),
		getReviews(fetch, params.slug)
	]);

	if (bookRes.error) {
		throw error(bookRes.error.status || 500, bookRes.error.detail);
	}

	const book = bookRes.data!;

	// Load in parallel: extraction (if ready) + shelf status (if logged in)
	const [extractionRes, shelfRes] = await Promise.all([
		book.ai_extraction_status === 'ready' ? getExtraction(fetch, book.id) : Promise.resolve(null),
		user ? getShelfEntry(fetch, book.id) : Promise.resolve(null)
	]);

	return {
		book,
		reviews: reviewsRes.data ?? { data: [], page: 1, per_page: 20, total: 0 },
		extraction: extractionRes?.data ?? null,
		shelfStatus: (shelfRes?.data?.status ?? 'none') as ShelfStatus | 'none'
	};
};
