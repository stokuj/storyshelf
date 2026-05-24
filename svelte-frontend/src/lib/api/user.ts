import { apiFetch } from './_client';

export interface UserMe {
	id: number;
	handle: string;
	display_name: string;
	email: string;
	email_verified: boolean;
	bio: string | null;
	avatar_url: string | null;
	joined_at: string;
	followers_count: number;
	following_count: number;
}

export async function getCurrentUser(fetchFn: typeof fetch) {
	return apiFetch<UserMe>(fetchFn, '/users/me/', undefined, true);
}
