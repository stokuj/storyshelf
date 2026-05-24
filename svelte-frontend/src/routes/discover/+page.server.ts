import type { PageServerLoad } from './$types';
import { listBooks } from '$lib/api/books';

export const load: PageServerLoad = async ({ fetch, url }) => {
	const q = url.searchParams.get('q') ?? '';
	const genre = url.searchParams.get('genre') ?? '';
	const sort = url.searchParams.get('sort') ?? 'title';
	const page = Number(url.searchParams.get('page') ?? 1);

	const { data: books, error } = await listBooks(fetch, { q, genre, sort, page });

	if (error) {
		return { books: { data: [] as never[], page: 1, per_page: 20, total: 0 } };
	}

	return { books };
};
