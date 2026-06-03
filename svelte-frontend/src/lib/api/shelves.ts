import { apiFetch } from './_client';
import type {
	Shelf,
	ShelfDetail,
	ShelfCreate,
	ShelfUpdate,
	PublicShelf,
	PublicShelfDetail,
	ShelfBook
} from '$lib/types/shelf';

/** Current user's custom shelves. Pass bookSlug to get `contains_book` per shelf. */
export function fetchMyShelves(fetchFn: typeof fetch, bookSlug?: string, isServerSide = false) {
	const q = bookSlug ? `?book_slug=${encodeURIComponent(bookSlug)}` : '';
	return apiFetch<Shelf[]>(fetchFn, `/shelves/${q}`, undefined, isServerSide);
}

export function fetchMyShelf(fetchFn: typeof fetch, slug: string, isServerSide = false) {
	return apiFetch<ShelfDetail>(fetchFn, `/shelves/${slug}/`, undefined, isServerSide);
}

export function createShelf(fetchFn: typeof fetch, data: ShelfCreate) {
	return apiFetch<Shelf>(fetchFn, '/shelves/', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

export function updateShelf(fetchFn: typeof fetch, slug: string, data: ShelfUpdate) {
	return apiFetch<Shelf>(fetchFn, `/shelves/${slug}/`, {
		method: 'PATCH',
		body: JSON.stringify(data)
	});
}

export function deleteShelf(fetchFn: typeof fetch, slug: string) {
	return apiFetch<null>(fetchFn, `/shelves/${slug}/`, { method: 'DELETE' });
}

export function addBookToShelf(fetchFn: typeof fetch, slug: string, bookSlug: string) {
	return apiFetch<ShelfBook>(fetchFn, `/shelves/${slug}/books/`, {
		method: 'POST',
		body: JSON.stringify({ book_slug: bookSlug })
	});
}

export function removeBookFromShelf(fetchFn: typeof fetch, slug: string, bookSlug: string) {
	return apiFetch<null>(fetchFn, `/shelves/${slug}/books/${bookSlug}/`, { method: 'DELETE' });
}

/** Public shelves of a user (by handle). */
export function fetchPublicShelves(fetchFn: typeof fetch, handle: string, isServerSide = false) {
	return apiFetch<PublicShelf[]>(fetchFn, `/u/${handle}/shelves/`, undefined, isServerSide);
}

export function fetchPublicShelf(
	fetchFn: typeof fetch,
	handle: string,
	slug: string,
	isServerSide = false
) {
	return apiFetch<PublicShelfDetail>(
		fetchFn,
		`/u/${handle}/shelves/${slug}/`,
		undefined,
		isServerSide
	);
}
