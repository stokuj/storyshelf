import { apiFetch } from './_client';

export type ShelfStatus = 'WANT_TO_READ' | 'READING' | 'READ';

export interface ShelfEntry {
	book: string;
	status: ShelfStatus;
	created_at: string;
}

export async function getMyShelves(fetchFn: typeof fetch) {
	return apiFetch<ShelfEntry[]>(fetchFn, '/shelf/', undefined, true);
}

export async function getShelfEntry(fetchFn: typeof fetch, bookId: number) {
	return apiFetch<ShelfEntry>(fetchFn, `/shelf/${bookId}/`, undefined, true);
}

export async function addToShelf(fetchFn: typeof fetch, bookId: number) {
	return apiFetch<Record<string, never>>(fetchFn, `/shelf/${bookId}/`, { method: 'POST' }, true);
}

export async function removeFromShelf(fetchFn: typeof fetch, bookId: number) {
	return apiFetch<Record<string, never>>(fetchFn, `/shelf/${bookId}/`, { method: 'DELETE' }, true);
}

export async function updateShelfEntry(fetchFn: typeof fetch, bookId: number, status: string) {
	return apiFetch<Record<string, never>>(
		fetchFn,
		`/shelf/${bookId}/`,
		{
			method: 'PATCH',
			body: JSON.stringify({ status })
		},
		true
	);
}
