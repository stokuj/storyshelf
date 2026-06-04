import { apiFetch } from './_client';

export interface UserStats {
	status_counts: { want_to_read: number; reading: number; read: number };
	totals: { pages_read: number; avg_rating_given: number | null };
	books_per_year: { year: number; count: number }[];
	rating_distribution: { rating: number; count: number }[];
	time_on_shelf_days: number | null;
}

export function getMyStats(fetchFn: typeof fetch, isServerSide = false) {
	return apiFetch<UserStats>(fetchFn, '/users/me/stats/', undefined, isServerSide);
}
