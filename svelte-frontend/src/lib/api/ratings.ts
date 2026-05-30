import { apiFetch } from './_client';
import type { RatingResponse } from '$lib/types/shelf';

/** All of the current user's ratings (plain list). */
export function fetchRatings(fetchFn: typeof fetch, isServerSide = false) {
	return apiFetch<RatingResponse[]>(fetchFn, '/ratings/', undefined, isServerSide);
}

/** The current user's rating for one book, or null. */
export async function fetchUserRating(
	fetchFn: typeof fetch,
	bookSlug: string,
	isServerSide = false
) {
	const { data, error } = await apiFetch<RatingResponse[]>(
		fetchFn,
		`/ratings/?book_slug=${encodeURIComponent(bookSlug)}`,
		undefined,
		isServerSide
	);
	return { data: data && data.length > 0 ? data[0] : null, error };
}

/** Upsert (PUT). 201 create / 200 update — both return the rating row. */
export function upsertRating(fetchFn: typeof fetch, bookSlug: string, rating: number) {
	return apiFetch<RatingResponse>(fetchFn, '/ratings/', {
		method: 'PUT',
		body: JSON.stringify({ book_slug: bookSlug, rating })
	});
}

export function deleteRatingById(fetchFn: typeof fetch, id: number) {
	return apiFetch<null>(fetchFn, `/ratings/${id}/`, { method: 'DELETE' });
}
