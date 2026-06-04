import type { PageServerLoad } from './$types';
import { listUsers } from '$lib/api/user';

export const load: PageServerLoad = async ({ fetch, url }) => {
	const search = url.searchParams.get('search') ?? '';
	const ordering = url.searchParams.get('ordering') ?? '-followers_count';

	const { data, error } = await listUsers(
		fetch,
		{ search: search || undefined, ordering, page: 1, perPage: 20 },
		true
	);

	return {
		initialUsers: data?.data ?? [],
		initialTotal: data?.total ?? 0,
		initialSearch: search,
		initialOrdering: ordering,
		loadError: error ? { status: error.status, detail: error.detail } : null
	};
};
