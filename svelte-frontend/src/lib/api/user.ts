import { apiFetch } from './_client';

export interface UserMe {
	id: number;
	handle: string;
	display_name: string;
	email: string;
	bio: string;
	avatar_url: string | null;
	member_since: string;
	settings: { profile_public: boolean };
}

export async function getCurrentUser(fetchFn: typeof fetch) {
	return apiFetch<UserMe>(fetchFn, '/users/me/', undefined, true);
}
