import { request as playwrightRequest } from '@playwright/test';
import { writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const BASE_API_URL = process.env.TEST_API_URL ?? 'http://localhost:8000';
const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL ?? 'admin@e2e.test';
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD ?? 'admin123';

interface SeedBook {
	title: string;
	year: number;
	description: string;
	cover_url: string;
	authors: string[];
	genres: string[];
	tags: string[];
	avg_rating?: number;
}

const BOOK_SEED: SeedBook[] = [
	{
		title: 'The Fellowship of the Ring',
		year: 1954,
		description:
			'The first volume of The Lord of the Rings trilogy. Frodo Baggins inherits the One Ring from his uncle Bilbo and must embark on a perilous journey to destroy it.',
		cover_url: 'https://covers.openlibrary.org/b/id/8473676-L.jpg',
		authors: ['J.R.R. Tolkien'],
		genres: ['Fantasy'],
		tags: ['classic', 'epic'],
		avg_rating: 4.5
	},
	{
		title: 'Dune',
		year: 1965,
		description:
			'Set on the desert planet Arrakis, Dune is the story of Paul Atreides, a young nobleman thrust into a complex political struggle over the most valuable substance in the universe.',
		cover_url: 'https://covers.openlibrary.org/b/id/11153217-L.jpg',
		authors: ['Frank Herbert'],
		genres: ['Science Fiction'],
		tags: ['classic', 'political'],
		avg_rating: 4.2
	},
	{
		title: '1984',
		year: 1949,
		description:
			'A dystopian novel set in a totalitarian society ruled by Big Brother. Winston Smith struggles to maintain his humanity in a world of surveillance and mind control.',
		cover_url: 'https://covers.openlibrary.org/b/id/8225261-L.jpg',
		authors: ['George Orwell'],
		genres: ['Dystopian'],
		tags: ['classic', 'political'],
		avg_rating: 4.0
	}
];

export default async function globalSetup(): Promise<void> {
	const api = await playwrightRequest.newContext({ baseURL: BASE_API_URL });

	// 1. Healthcheck
	try {
		const healthRes = await api.get('/api/docs/', { timeout: 5_000 });
		if (!healthRes.ok()) {
			throw new Error(
				`Django backend responded with ${healthRes.status()}. Is dev stack running? Try: make dev-up`
			);
		}
		console.log('[e2e] Django backend healthcheck OK');
	} catch (err) {
		throw new Error(
			`Django backend not reachable at ${BASE_API_URL}. Start with: make dev-up`,
			{ cause: err }
		);
	}

	// 2. Admin login
	console.log('[e2e] Logging in as admin...');
	const loginRes = await api.post('/api/auth/login/', {
		data: { email: ADMIN_EMAIL, password: ADMIN_PASSWORD }
	});
	if (!loginRes.ok()) {
		const body = await loginRes.text();
		throw new Error(
			`[e2e] Admin login failed: ${loginRes.status()} ${body}. Create staff user first (Task 1).`
		);
	}
	console.log('[e2e] Admin login OK');

	// 3. Seed 3 books (idempotent)
	const slugs: Record<string, string> = {};
	for (const book of BOOK_SEED) {
		const checkRes = await api.get(
			`/api/books/?search=${encodeURIComponent(book.title)}&per_page=1`
		);
		if (checkRes.ok()) {
			const existing = await checkRes.json();
			if (existing.total > 0) {
				slugs[book.title] = existing.data[0].slug;
				console.log(`[e2e] Already exists: ${book.title} → ${existing.data[0].slug}`);
				continue;
			}
		}

		console.log(`[e2e] Seeding: ${book.title}...`);
		const res = await api.post('/api/books/', { data: book });
		if (!res.ok()) {
			const body = await res.text();
			throw new Error(`[e2e] Failed to seed "${book.title}": ${res.status()} ${body}`);
		}
		const data = await res.json();
		slugs[book.title] = data.slug;
		console.log(`[e2e]   → slug: ${data.slug}`);
	}

	// 4. Write slugs file
	const __dirname = dirname(fileURLToPath(import.meta.url));
	const slugsPath = resolve(__dirname, '.seed-slugs.json');
	writeFileSync(slugsPath, JSON.stringify(slugs, null, 2), 'utf-8');
	console.log(`[e2e] Slugs written to ${slugsPath}`);

	await api.dispose();
}
