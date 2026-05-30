import { redirect } from '@sveltejs/kit';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ parent, url }) => {
	const { user } = await parent();
	if (!user) {
		throw redirect(303, `/login?next=${encodeURIComponent(url.pathname)}`);
	}
	return { user };
};
