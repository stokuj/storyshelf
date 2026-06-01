import { apiFetch } from './_client';

export interface UserMe {
	id: number;
	handle: string;
	display_name: string;
	email: string;
	bio: string | null;
	avatar_url: string | null;
}

export async function getCurrentUser(fetchFn: typeof fetch) {
	return apiFetch<UserMe>(fetchFn, '/users/me/', undefined, true);
}
