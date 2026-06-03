import { apiFetch } from './_client';
import type { FollowUser } from '$lib/types/follow';

export function followUser(fetchFn: typeof fetch, handle: string) {
	return apiFetch<{ follower_handle: string; following_handle: string }>(
		fetchFn,
		`/users/${handle}/follow/`,
		{ method: 'POST' }
	);
}

export function unfollowUser(fetchFn: typeof fetch, handle: string) {
	return apiFetch<null>(fetchFn, `/users/${handle}/follow/`, { method: 'DELETE' });
}

export function fetchFollowers(fetchFn: typeof fetch, handle: string, isServerSide = false) {
	return apiFetch<FollowUser[]>(fetchFn, `/users/${handle}/followers/`, undefined, isServerSide);
}

export function fetchFollowing(fetchFn: typeof fetch, handle: string, isServerSide = false) {
	return apiFetch<FollowUser[]>(fetchFn, `/users/${handle}/following/`, undefined, isServerSide);
}
