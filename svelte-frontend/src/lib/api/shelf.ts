import { apiFetch } from './_client';
import type { PublicShelfEntry, ShelfEntry, ShelfEntryUpdate, ShelfStatus } from '$lib/types/shelf';

export function fetchShelfEntries(fetchFn: typeof fetch, isServerSide = false) {
	return apiFetch<ShelfEntry[]>(fetchFn, '/shelf/entries/', undefined, isServerSide);
}

/** Another user's public default reading shelf (M11). */
export function fetchPublicShelf(fetchFn: typeof fetch, handle: string, isServerSide = false) {
	return apiFetch<PublicShelfEntry[]>(fetchFn, `/u/${handle}/shelf/`, undefined, isServerSide);
}

/** The current user's shelf entry for one book, or null. */
export async function fetchShelfEntry(
	fetchFn: typeof fetch,
	bookSlug: string,
	isServerSide = false
) {
	const { data, error } = await apiFetch<ShelfEntry[]>(
		fetchFn,
		`/shelf/entries/?book_slug=${encodeURIComponent(bookSlug)}`,
		undefined,
		isServerSide
	);
	return { data: data && data.length > 0 ? data[0] : null, error };
}

export function addToShelf(
	fetchFn: typeof fetch,
	bookSlug: string,
	status: ShelfStatus = 'WANT_TO_READ'
) {
	return apiFetch<ShelfEntry>(fetchFn, '/shelf/entries/', {
		method: 'POST',
		body: JSON.stringify({ book_slug: bookSlug, status })
	});
}

export function updateShelfEntry(fetchFn: typeof fetch, id: number, data: ShelfEntryUpdate) {
	return apiFetch<ShelfEntry>(fetchFn, `/shelf/entries/${id}/`, {
		method: 'PATCH',
		body: JSON.stringify(data)
	});
}

export function deleteShelfEntry(fetchFn: typeof fetch, id: number) {
	return apiFetch<null>(fetchFn, `/shelf/entries/${id}/`, { method: 'DELETE' });
}
