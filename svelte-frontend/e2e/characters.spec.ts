import { test, expect } from './fixtures';
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const slugs = JSON.parse(readFileSync(resolve(__dirname, '.seed-slugs.json'), 'utf-8'));
const FELLOWSHIP = slugs['The Fellowship of the Ring'];

// Characters are seeded deterministically via `manage.py seed_characters <slug>`
// (no live LLM). The CI e2e job runs that command after global setup; locally
// run it against the dev stack. Skips if the analysis was not seeded.
test.describe('Character analysis', () => {
	test('renders seeded characters and the detail page', async ({ page, request }) => {
		test.skip(!FELLOWSHIP, 'Fellowship book not seeded');
		// Skip gracefully if the analysis was not seeded (e.g. a local run without
		// the backend CLI/DB env); CI seeds it in global setup.
		const probe = await request.get(`/api/books/${FELLOWSHIP}/characters/`);
		const seeded = probe.ok() ? await probe.json() : { status: null, characters: [] };
		test.skip(seeded.status !== 'done' || !seeded.characters?.length, 'characters not seeded');

		await page.goto(`/books/${FELLOWSHIP}`);

		await expect(page.getByRole('heading', { name: 'Characters' })).toBeVisible();
		const frodoCard = page.getByRole('link', { name: /Frodo/ });
		await expect(frodoCard).toBeVisible();
		await expect(page.getByRole('link', { name: /Sam/ })).toBeVisible();

		await frodoCard.click();
		await expect(page).toHaveURL(/\/characters\//);
		await expect(page.getByRole('heading', { name: 'Frodo' })).toBeVisible();
		await expect(page.getByText('Ring-bearer')).toBeVisible();
	});
});
