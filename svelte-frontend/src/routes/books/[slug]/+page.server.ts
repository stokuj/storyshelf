import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { getBook, getReviews } from '$lib/api/books';
import { getExtraction } from '$lib/api/ai';

export const load: PageServerLoad = async ({ fetch, params }) => {
	const [bookRes, reviewsRes] = await Promise.all([
		getBook(fetch, params.slug),
		getReviews(fetch, params.slug)
	]);

	if (bookRes.error) {
		throw error(bookRes.error.status || 500, bookRes.error.detail);
	}

	// Lazy: only load extraction if status is 'ready'
	let extractionRes = null;
	if (bookRes.data?.ai_extraction_status === 'ready') {
		extractionRes = await getExtraction(fetch, bookRes.data.id);
	}

	return {
		book: bookRes.data,
		reviews: reviewsRes.data ?? { data: [], page: 1, per_page: 20, total: 0 },
		extraction: extractionRes?.data ?? null
	};
};
