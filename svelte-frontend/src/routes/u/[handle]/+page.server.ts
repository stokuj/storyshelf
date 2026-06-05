import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { apiFetch } from '$lib/api/_client';
import { fetchPublicShelves } from '$lib/api/shelves';
import { fetchPublicShelf } from '$lib/api/shelf';
import { fetchUserReviews } from '$lib/api/reviews';
import type { User } from '$lib/types';

export const load: PageServerLoad = async ({ fetch, params, parent }) => {
	const { data: profile, error: profileErr } = await apiFetch<User>(
		fetch,
		`/u/${params.handle}/`,
		undefined,
		true
	);
	if (profileErr) {
		throw error(profileErr.status === 404 ? 404 : 500, profileErr.detail);
	}

	const { user: viewer } = await parent();
	const isOwner = viewer?.handle === params.handle;
	const isLoggedIn = !!viewer;

	// Independent reads — run them concurrently rather than serially.
	const [{ data: shelves }, { data: reading }, { data: reviews }] = await Promise.all([
		fetchPublicShelves(fetch, params.handle, true),
		fetchPublicShelf(fetch, params.handle, true),
		fetchUserReviews(fetch, params.handle, 1, true)
	]);

	return {
		profile,
		isOwner,
		isLoggedIn,
		shelves: shelves ?? [],
		reading: reading ?? [],
		reviews: reviews?.data ?? []
	};
};
