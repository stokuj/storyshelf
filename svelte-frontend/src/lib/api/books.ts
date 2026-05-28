import { apiFetch } from './_client';
import type { Book } from '$lib/types';

export interface PaginatedResponse<T> {
	data: T[];
	page: number;
	per_page: number;
	total: number;
}

export interface Genre {
	id: number;
	name: string;
	created_at: string;
}

export interface ListBooksParams {
	q?: string;
	genre?: string;
	author?: string;
	sort?: string;
	page?: number;
	perPage?: number;
}

const SORT_MAP: Record<string, string> = {
	rating: '-avg_rating',
	recent: '-year',
	title: 'title'
};

export async function listBooks(fetchFn: typeof fetch, params: ListBooksParams = {}) {
	const searchParams = new URLSearchParams();
	if (params.q) searchParams.set('search', params.q);
	if (params.genre) searchParams.set('genre', params.genre);
	if (params.author) searchParams.set('author', params.author);
	const ordering = SORT_MAP[params.sort ?? ''] ?? params.sort;
	if (ordering) searchParams.set('ordering', ordering);
	if (params.page) searchParams.set('page', String(params.page));
	if (params.perPage) searchParams.set('per_page', String(params.perPage));

	const qs = searchParams.toString();
	return apiFetch<PaginatedResponse<Book>>(
		fetchFn,
		`/books/${qs ? '?' + qs : ''}`,
		undefined,
		true
	);
}

export async function fetchGenres(fetchFn: typeof fetch) {
	return apiFetch<PaginatedResponse<Genre>>(fetchFn, '/genres/?per_page=100', undefined, true);
}

export async function getBook(fetchFn: typeof fetch, idOrSlug: string) {
	return apiFetch<Book>(fetchFn, `/books/${idOrSlug}/`, undefined, true);
}

export async function getReviews(fetchFn: typeof fetch, idOrSlug: string, page = 1) {
	return apiFetch<
		PaginatedResponse<{
			id: number;
			rating: number;
			content: string;
			createdAt: string;
			handle: string;
			bookTitle: string;
		}>
	>(fetchFn, `/books/${idOrSlug}/reviews/?page=${page}`, undefined, true);
}

export async function createReview(
	fetchFn: typeof fetch,
	idOrSlug: string,
	data: { rating: number; content: string }
) {
	return apiFetch<{ id: number }>(
		fetchFn,
		`/books/${idOrSlug}/reviews/`,
		{
			method: 'POST',
			body: JSON.stringify(data)
		},
		true
	);
}

export async function searchByCharacter(fetchFn: typeof fetch, name: string) {
	return apiFetch<PaginatedResponse<Book>>(
		fetchFn,
		`/books/contains-character/?name=${encodeURIComponent(name)}`,
		undefined,
		true
	);
}
