import { getCurrentUser } from '$lib/api/user';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch }) => {
	const { data: user } = await getCurrentUser(fetch);
	return { user };
};
