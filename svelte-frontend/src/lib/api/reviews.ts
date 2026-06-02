import { apiFetch } from './_client';
import type { PaginatedResponse } from './books';
import type { Review } from '$lib/types/review';

/** Public, paginated list of reviews for one book (newest first). */
export function fetchReviews(
	fetchFn: typeof fetch,
	bookSlug: string,
	page = 1,
	isServerSide = false
) {
	return apiFetch<PaginatedResponse<Review>>(
		fetchFn,
		`/reviews/?book_slug=${encodeURIComponent(bookSlug)}&page=${page}`,
		undefined,
		isServerSide
	);
}

/** The current user's review for one book, or null (404 → null). */
export async function fetchMyReview(fetchFn: typeof fetch, bookSlug: string, isServerSide = false) {
	const { data, error } = await apiFetch<Review>(
		fetchFn,
		`/reviews/me/?book_slug=${encodeURIComponent(bookSlug)}`,
		undefined,
		isServerSide
	);
	if (error?.status === 404) return { data: null, error: null };
	return { data, error };
}

/** Upsert (PUT). 201 create / 200 update — both return the review row. */
export function upsertReview(fetchFn: typeof fetch, bookSlug: string, body: string) {
	return apiFetch<Review>(fetchFn, '/reviews/', {
		method: 'PUT',
		body: JSON.stringify({ book_slug: bookSlug, body })
	});
}

export function deleteReview(fetchFn: typeof fetch, id: number) {
	return apiFetch<null>(fetchFn, `/reviews/${id}/`, { method: 'DELETE' });
}
