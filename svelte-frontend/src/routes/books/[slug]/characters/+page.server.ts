import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { getBook } from '$lib/api/books';
import { getBookCharacters } from '$lib/api/characters';

export const load: PageServerLoad = async ({ fetch, params }) => {
	const bookRes = await getBook(fetch, params.slug);
	if (bookRes.error) throw error(bookRes.error.status || 500, bookRes.error.detail);

	const charsRes = await getBookCharacters(fetch, bookRes.data!.id);

	return {
		book: bookRes.data,
		characters: charsRes.data ?? []
	};
};
