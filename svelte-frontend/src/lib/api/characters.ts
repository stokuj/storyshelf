import { apiFetch } from './_client';
import type { CharacterDetail, CharacterListResponse } from '$lib/types/character';

/** Status + characters for one book (public). */
export function fetchCharacters(fetchFn: typeof fetch, bookSlug: string, isServerSide = false) {
	return apiFetch<CharacterListResponse>(
		fetchFn,
		`/books/${encodeURIComponent(bookSlug)}/characters/`,
		undefined,
		isServerSide
	);
}

/** One character + its relations (public). */
export function fetchCharacter(
	fetchFn: typeof fetch,
	bookSlug: string,
	charSlug: string,
	isServerSide = false
) {
	return apiFetch<CharacterDetail>(
		fetchFn,
		`/books/${encodeURIComponent(bookSlug)}/characters/${encodeURIComponent(charSlug)}/`,
		undefined,
		isServerSide
	);
}

/** Enqueue generation (auth). Returns the new analysis status. */
export function generateCharacters(fetchFn: typeof fetch, bookSlug: string) {
	return apiFetch<{ status: string }>(
		fetchFn,
		`/books/${encodeURIComponent(bookSlug)}/characters/generate/`,
		{ method: 'POST' }
	);
}
