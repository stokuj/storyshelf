import { apiFetch } from './_client';
import type { AIExtraction } from '$lib/types';

export async function runExtraction(fetchFn: typeof fetch, bookId: string | number) {
	return apiFetch<AIExtraction>(fetchFn, `/books/${bookId}/ai/extract/`, { method: 'POST' }, true);
}

export async function getExtraction(fetchFn: typeof fetch, bookId: string | number) {
	return apiFetch<AIExtraction>(fetchFn, `/books/${bookId}/ai/extraction/`, undefined, true);
}

export async function refreshExtraction(fetchFn: typeof fetch, bookId: string | number) {
	return apiFetch<AIExtraction>(
		fetchFn,
		`/books/${bookId}/ai/extract/refresh/`,
		{ method: 'POST' },
		true
	);
}

export async function verifyCharacter(
	fetchFn: typeof fetch,
	bookId: string | number,
	characterId: string | number
) {
	return apiFetch<Record<string, never>>(
		fetchFn,
		`/books/${bookId}/ai/extraction/${characterId}/verify/`,
		{ method: 'POST' },
		true
	);
}

export async function rejectCharacter(
	fetchFn: typeof fetch,
	bookId: string | number,
	characterId: string | number
) {
	return apiFetch<Record<string, never>>(
		fetchFn,
		`/books/${bookId}/ai/extraction/${characterId}/reject/`,
		{ method: 'POST' },
		true
	);
}
