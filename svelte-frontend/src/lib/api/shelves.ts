import { apiFetch } from './_client';

export async function getMyShelves(fetchFn: typeof fetch) {
	return apiFetch<{ book: string; status: string; createdAt: string }[]>(
		fetchFn,
		'/shelf/',
		undefined,
		true
	);
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
