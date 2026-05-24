import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { getBook } from '$lib/api/books';
import { getCharacter, getBookRelations } from '$lib/api/characters';

export const load: PageServerLoad = async ({ fetch, params }) => {
	const [bookRes, charRes] = await Promise.all([
		getBook(fetch, params.slug),
		getCharacter(fetch, params.charId)
	]);

	if (bookRes.error) throw error(bookRes.error.status || 500, bookRes.error.detail);
	if (charRes.error) throw error(charRes.error.status || 500, charRes.error.detail);

	const relationsRes = await getBookRelations(fetch, bookRes.data!.id);

	return {
		book: bookRes.data,
		character: charRes.data,
		relations: relationsRes.data ?? []
	};
};
