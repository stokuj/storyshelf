import { apiFetch } from './_client';
import type { PaginatedResponse } from './books';

export interface UserMe {
	id: number;
	handle: string;
	display_name: string;
	email: string;
	bio: string | null;
	avatar_url: string | null;
	member_since: string;
	profile_public: boolean;
}

export async function getCurrentUser(fetchFn: typeof fetch) {
	return apiFetch<UserMe>(fetchFn, '/users/me/', undefined, true);
}

export interface UserListItem {
	handle: string;
	display_name: string;
	avatar_url: string | null;
	followers_count: number;
}

export interface ListUsersParams {
	search?: string;
	ordering?: string;
	page?: number;
	perPage?: number;
}

export async function listUsers(
	fetchFn: typeof fetch,
	params: ListUsersParams = {},
	isServerSide = false
) {
	const sp = new URLSearchParams();
	if (params.search) sp.set('search', params.search);
	if (params.ordering) sp.set('ordering', params.ordering);
	if (params.page) sp.set('page', String(params.page));
	if (params.perPage) sp.set('per_page', String(params.perPage));
	const qs = sp.toString();
	return apiFetch<PaginatedResponse<UserListItem>>(
		fetchFn,
		`/users/${qs ? `?${qs}` : ''}`,
		undefined,
		isServerSide
	);
}
