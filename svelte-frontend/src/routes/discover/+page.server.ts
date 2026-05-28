import type { PageServerLoad } from './$types';
import { listBooks } from '$lib/api/books';

export const load: PageServerLoad = async ({ fetch, url }) => {
	const q = url.searchParams.get('q') ?? '';
	const genre = url.searchParams.get('genre') ?? '';
	const sort = url.searchParams.get('sort') ?? '';
	const author = url.searchParams.get('author') ?? '';

	const { data, error } = await listBooks(fetch, {
		q: q || undefined,
		genre: genre || undefined,
		author: author || undefined,
		sort: sort || undefined,
		page: 1,
		perPage: 12
	});

	return {
		initialBooks: data?.data ?? [],
		initialPage: data?.page ?? 1,
		initialPerPage: data?.per_page ?? 12,
		initialTotal: data?.total ?? 0,
		initialQ: q,
		initialGenre: genre,
		initialSort: sort,
		initialAuthor: author,
		loadError: error ? { status: error.status, detail: error.detail } : null
	};
};
