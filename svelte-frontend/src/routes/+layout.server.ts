import { getCurrentUser } from '$lib/api/user';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ fetch }) => {
	const { data: user, error } = await getCurrentUser(fetch);
	return { user, authError: error };
};
