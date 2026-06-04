import { apiFetch } from './_client';
import type { FollowUser } from '$lib/types/follow';

export function followUser(fetchFn: typeof fetch, handle: string) {
	return apiFetch<{ follower_handle: string; following_handle: string }>(
		fetchFn,
		`/u/${handle}/follow/`,
		{ method: 'POST' }
	);
}

export function unfollowUser(fetchFn: typeof fetch, handle: string) {
	return apiFetch<null>(fetchFn, `/u/${handle}/follow/`, { method: 'DELETE' });
}

export function fetchFollowers(fetchFn: typeof fetch, handle: string, isServerSide = false) {
	return apiFetch<FollowUser[]>(fetchFn, `/u/${handle}/followers/`, undefined, isServerSide);
}

export function fetchFollowing(fetchFn: typeof fetch, handle: string, isServerSide = false) {
	return apiFetch<FollowUser[]>(fetchFn, `/u/${handle}/following/`, undefined, isServerSide);
}
