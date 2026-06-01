import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { getBook } from '$lib/api/books';
import { fetchUserRating } from '$lib/api/ratings';
import { fetchShelfEntry } from '$lib/api/shelf';
import { fetchReviews, fetchMyReview } from '$lib/api/reviews';

export const load: PageServerLoad = async ({ fetch, params, parent }) => {
	const { user } = await parent();

	const [bookRes, ratingRes, entryRes, reviewsRes, myReviewRes] = await Promise.all([
		getBook(fetch, params.slug),
		user ? fetchUserRating(fetch, params.slug, true) : Promise.resolve({ data: null, error: null }),
		user ? fetchShelfEntry(fetch, params.slug, true) : Promise.resolve({ data: null, error: null }),
		fetchReviews(fetch, params.slug, 1, true),
		user ? fetchMyReview(fetch, params.slug, true) : Promise.resolve({ data: null, error: null })
	]);

	if (bookRes.error) {
		throw error(bookRes.error.status || 500, bookRes.error.detail);
	}

	return {
		book: bookRes.data!,
		user,
		userRating: ratingRes.data ? { id: ratingRes.data.id, rating: ratingRes.data.rating } : null,
		shelfEntry: entryRes.data ?? null,
		reviews: reviewsRes.data?.data ?? [],
		reviewsTotal: reviewsRes.data?.total ?? 0,
		myReview: myReviewRes.data ?? null
	};
};
