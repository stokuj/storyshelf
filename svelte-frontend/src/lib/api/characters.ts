import { apiFetch } from './_client';
import type { Character, Relation } from '$lib/types';

export async function getBookCharacters(fetchFn: typeof fetch, bookId: string | number) {
	return apiFetch<Character[]>(fetchFn, `/books/${bookId}/characters/`, undefined, true);
}

export async function getBookRelations(fetchFn: typeof fetch, bookId: string | number) {
	return apiFetch<Relation[]>(fetchFn, `/books/${bookId}/relations/`, undefined, true);
}

export async function getCharacter(fetchFn: typeof fetch, charId: string | number) {
	return apiFetch<Character>(fetchFn, `/characters/${charId}/`, undefined, true);
}

export async function updateCharacter(
	fetchFn: typeof fetch,
	charId: string | number,
	data: Partial<Character>
) {
	return apiFetch<Character>(
		fetchFn,
		`/characters/${charId}/`,
		{
			method: 'PATCH',
			body: JSON.stringify(data)
		},
		true
	);
}
