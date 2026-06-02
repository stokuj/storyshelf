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
