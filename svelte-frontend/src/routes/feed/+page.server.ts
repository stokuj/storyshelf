import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { fetchFeed } from '$lib/api/feed';

export const load: PageServerLoad = async ({ fetch, parent, url }) => {
	const { user } = await parent();
	if (!user) {
		throw redirect(303, `/login?next=${encodeURIComponent(url.pathname)}`);
	}
	const { data } = await fetchFeed(fetch, undefined, true);
	return {
		items: data?.results ?? [],
		nextBefore: data?.next_before ?? null
	};
};
