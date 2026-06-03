import { type Cookie } from '@playwright/test';
import { API_BASE_URL } from '../fixtures';

export interface SeedShelfEntry {
	id: number;
	book_slug: string;
	status: string;
	current_page: number | null;
}

export async function seedShelfEntry(
	entry: { book_slug: string; status: string; current_page?: number | null },
	cookies: Cookie[],
	playwright: typeof import('@playwright/test').playwright
): Promise<SeedShelfEntry> {
	const api = await playwright.request.newContext({
		baseURL: API_BASE_URL,
		storageState: { cookies, origins: [] }
	});
	const payload: Record<string, unknown> = { book_slug: entry.book_slug, status: entry.status };
	if (entry.current_page != null) payload.current_page = entry.current_page;
	const res = await api.post('/api/shelf/entries/', { data: payload });
	if (!res.ok()) {
		const body = await res.text();
		await api.dispose();
		throw new Error(
			`[seed] shelf entry failed: ${res.status()} ${body} payload=${JSON.stringify(payload)}`
		);
	}
	const data = await res.json();
	await api.dispose();
	return {
		id: data.id,
		book_slug: data.book.slug,
		status: data.status,
		current_page: data.current_page
	};
}

export async function cleanupShelfEntries(
	cookies: Cookie[],
	playwright: typeof import('@playwright/test').playwright
): Promise<void> {
	const api = await playwright.request.newContext({
		baseURL: API_BASE_URL,
		storageState: { cookies, origins: [] }
	});
	const listRes = await api.get('/api/shelf/entries/');
	if (listRes.ok()) {
		const entries: { id: number }[] = await listRes.json();
		for (const e of entries) await api.delete(`/api/shelf/entries/${e.id}/`);
	}
	await api.dispose();
}

export interface SeedShelf {
	slug: string;
	name: string;
}

/** Create a custom shelf via API and optionally add books to it. Returns the shelf slug. */
export async function seedShelf(
	shelf: { name: string; is_public?: boolean; book_slugs?: string[] },
	cookies: Cookie[],
	playwright: typeof import('@playwright/test').playwright
): Promise<SeedShelf> {
	const api = await playwright.request.newContext({
		baseURL: API_BASE_URL,
		storageState: { cookies, origins: [] }
	});
	const res = await api.post('/api/shelves/', {
		data: { name: shelf.name, is_public: shelf.is_public ?? false }
	});
	if (!res.ok()) {
		const body = await res.text();
		await api.dispose();
		throw new Error(`[seed] shelf create failed: ${res.status()} ${body}`);
	}
	const data = await res.json();
	for (const bookSlug of shelf.book_slugs ?? []) {
		const addRes = await api.post(`/api/shelves/${data.slug}/books/`, {
			data: { book_slug: bookSlug }
		});
		if (!addRes.ok()) {
			const body = await addRes.text();
			await api.dispose();
			throw new Error(`[seed] add book to shelf failed: ${addRes.status()} ${body}`);
		}
	}
	await api.dispose();
	return { slug: data.slug, name: data.name };
}

/** Delete all custom shelves owned by the user holding these cookies. */
export async function cleanupShelves(
	cookies: Cookie[],
	playwright: typeof import('@playwright/test').playwright
): Promise<void> {
	const api = await playwright.request.newContext({
		baseURL: API_BASE_URL,
		storageState: { cookies, origins: [] }
	});
	const listRes = await api.get('/api/shelves/');
	if (listRes.ok()) {
		const shelves: { slug: string }[] = await listRes.json();
		for (const s of shelves) await api.delete(`/api/shelves/${s.slug}/`);
	}
	await api.dispose();
}

export async function cleanupMyReview(
	bookSlug: string,
	cookies: Cookie[],
	playwright: typeof import('@playwright/test').playwright
): Promise<void> {
	const api = await playwright.request.newContext({
		baseURL: API_BASE_URL,
		storageState: { cookies, origins: [] }
	});
	const res = await api.get(`/api/reviews/me/?book_slug=${bookSlug}`);
	if (res.ok()) {
		const review = await res.json();
		await api.delete(`/api/reviews/${review.id}/`);
	}
	await api.dispose();
}
