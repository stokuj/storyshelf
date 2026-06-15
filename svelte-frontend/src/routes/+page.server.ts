import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { fetchShelfEntries } from '$lib/api/shelf';
import { fetchFeed } from '$lib/api/feed';

export const load: PageServerLoad = async ({ fetch, parent }) => {
	const { user } = await parent();
	// Guests have no personalized home; send them straight to the catalog.
	if (!user) {
		throw redirect(307, '/discover');
	}

	const [entriesRes, feedRes] = await Promise.all([
		fetchShelfEntries(fetch, true),
		fetchFeed(fetch, undefined, true)
	]);

	const reading = (entriesRes.data ?? []).filter((e) => e.status === 'READING');

	return {
		reading,
		feedItems: (feedRes.data?.results ?? []).slice(0, 5)
	};
};
