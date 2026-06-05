import { apiFetch } from './_client';
import type { FeedResponse } from '$lib/types/feed';

export function fetchFeed(fetchFn: typeof fetch, before?: string, isServerSide = false) {
	const qs = before ? `?before=${encodeURIComponent(before)}` : '';
	return apiFetch<FeedResponse>(fetchFn, `/feed/${qs}`, undefined, isServerSide);
}
