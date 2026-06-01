# Post-M3 Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire up four half-built user stories (data export, account delete, avatar upload, reading progress), remove dead code, and align frontend user types with the backend contract.

**Architecture:** Pure cleanup/wiring on existing M1–M3 code. Export is delivered via a new SvelteKit `+server.ts` proxy route that forwards auth cookies to the backend and streams the ZIP. Delete uses a SvelteKit form action mirroring `logout`. Avatar/reading-progress are small client wirings to endpoints that already exist.

**Tech Stack:** SvelteKit 2 + Svelte 5 (runes), TypeScript, Django REST (backend, unchanged except one dead-class removal), Playwright (E2E), Vitest/svelte-check, ruff.

**Branch:** `fix/post-m3-settings-cleanup` (work continues here).

**Spec:** `docs/superpowers/specs/2026-06-01-post-m3-fixes-design.md`

---

## File Structure

**Group A — Wiring (create/modify):**
- Create: `svelte-frontend/src/routes/settings/data/export/+server.ts` — GET proxy that POSTs to backend export and streams ZIP back.
- Create: `svelte-frontend/src/routes/settings/data/+page.server.ts` — `delete` form action.
- Modify: `svelte-frontend/src/routes/settings/data/+page.svelte` — export link, password-based delete dialog.
- Modify: `svelte-frontend/src/routes/settings/+page.svelte` — avatar file input auto-submit; remove email_verified block (Group C).
- Modify: `svelte-frontend/src/lib/components/shelf/ShelfBookCard.svelte` — current_page input.
- Modify: `svelte-frontend/src/routes/shelf/+page.svelte` — `onProgressChange` handler.

**Group B — Dead code (delete/modify):**
- Delete: `svelte-frontend/src/lib/schemas/settings.ts`, `svelte-frontend/src/lib/schemas/user.ts`
- Delete: `svelte-frontend/src/lib/types/api.generated.ts`
- Delete: `svelte-frontend/src/routes/api/__mock/` (dir), `svelte-frontend/src/lib/api/__fixtures__/` (dir)
- Delete (backend): `BookPreviewSerializer` in `backend-django/books/serializers.py`
- Modify: `svelte-frontend/package.json` (drop `zod`), `svelte-frontend/.gitignore` (ignore generated types), `svelte-frontend/src/lib/components/shell/AppShell.svelte` (drop Search button).

**Group C — Type contracts (modify):**
- Modify: `svelte-frontend/src/lib/api/user.ts` (`UserMe`), `svelte-frontend/src/lib/types/user.ts` (`User`).

**Tests:**
- Modify: `svelte-frontend/e2e/settings.spec.ts`

> **Ordering note:** Do Group A first (adds behavior + E2E), then Group C (types — depends on A2 password dialog and removing email_verified), then Group B (deletions — `__fixtures__` referenced by `User` type, so delete after C is settled). Within each group, tasks are independent unless stated.

---

## Group A — Wiring

### Task A1: Data export download (proxy route + link)

**Files:**
- Create: `svelte-frontend/src/routes/settings/data/export/+server.ts`
- Modify: `svelte-frontend/src/routes/settings/data/+page.svelte:25-30`
- Test: `svelte-frontend/e2e/settings.spec.ts`

- [ ] **Step 1: Create the proxy route**

Create `svelte-frontend/src/routes/settings/data/export/+server.ts`:

```ts
import type { RequestHandler } from './$types';
import { serverApiBase } from '$lib/server/api';

// Proxies the authenticated ZIP export from the backend so the browser can
// download it directly. Cookies are forwarded to the backend by handleFetch
// (see src/hooks.server.ts). Backend endpoint is POST and returns application/zip.
export const GET: RequestHandler = async ({ fetch }) => {
	const res = await fetch(`${serverApiBase()}/users/me/export/`, {
		method: 'POST',
		credentials: 'include'
	});

	if (!res.ok) {
		return new Response(`Export failed (${res.status})`, { status: res.status });
	}

	return new Response(res.body, {
		status: 200,
		headers: {
			'Content-Type': res.headers.get('Content-Type') ?? 'application/zip',
			'Content-Disposition':
				res.headers.get('Content-Disposition') ?? 'attachment; filename="storyshelf-export.zip"'
		}
	});
};
```

- [ ] **Step 2: Replace the export form with a download link**

In `svelte-frontend/src/routes/settings/data/+page.svelte`, replace the export `<form>` block (lines 25-30) with:

```svelte
<Button href="/settings/data/export" variant="outline" size="sm" data-sveltekit-reload>
	<Download class="mr-2 size-4" />
	Export all data
</Button>
```

(`data-sveltekit-reload` forces a full browser navigation so the `Content-Disposition` download is honored instead of client-side routing.)

- [ ] **Step 3: Run check + lint**

Run: `cd svelte-frontend && npm run check && npm run lint`
Expected: 0 errors. (Pre-existing `state_referenced_locally` warnings are OK.)

- [ ] **Step 4: Add E2E assertion for the export download**

In `svelte-frontend/e2e/settings.spec.ts`, replace the `data page shows export and delete options` test body's export check by adding a download test. Add this test inside the `Settings` describe block:

```ts
test('export data triggers a zip download', async ({ page, authUser }) => {
	await page.goto('/settings/data');
	const downloadPromise = page.waitForEvent('download');
	await page.getByRole('link', { name: 'Export all data' }).click();
	const download = await downloadPromise;
	expect(download.suggestedFilename()).toMatch(/\.zip$/);
});
```

- [ ] **Step 5: Run the E2E test**

Run: `cd svelte-frontend && npx playwright test settings.spec.ts -g "export data triggers"`
Expected: PASS (a `.zip` download is observed).

- [ ] **Step 6: Commit**

```bash
git add svelte-frontend/src/routes/settings/data/export/+server.ts \
        svelte-frontend/src/routes/settings/data/+page.svelte \
        svelte-frontend/e2e/settings.spec.ts
git commit -m "feat: wire data export download"
```

---

### Task A2: Delete account (password action + dialog)

**Files:**
- Create: `svelte-frontend/src/routes/settings/data/+page.server.ts`
- Modify: `svelte-frontend/src/routes/settings/data/+page.svelte` (dialog + script)
- Test: `svelte-frontend/e2e/settings.spec.ts`

- [ ] **Step 1: Create the delete action**

Create `svelte-frontend/src/routes/settings/data/+page.server.ts`:

```ts
import { fail, redirect } from '@sveltejs/kit';
import type { Actions } from './$types';
import { serverApiBase } from '$lib/server/api';

async function apiError(res: Response): Promise<string> {
	const body = await res.json().catch(() => ({}));
	return body.detail ?? body.message ?? `Request failed (${res.status})`;
}

export const actions: Actions = {
	delete: async ({ request, fetch, cookies }) => {
		const data = await request.formData();
		const current_password = data.get('current_password') as string;

		const res = await fetch(`${serverApiBase()}/users/me/`, {
			method: 'DELETE',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ current_password }),
			credentials: 'include'
		});

		if (!res.ok) {
			return fail(res.status, { error: await apiError(res) });
		}

		cookies.delete('access_token', { path: '/' });
		cookies.delete('refresh_token', { path: '/' });
		throw redirect(303, '/');
	}
};
```

- [ ] **Step 2: Switch the dialog to collect the password**

In `svelte-frontend/src/routes/settings/data/+page.svelte`:

Remove the now-unused state line `let deleteHandle = $state('');` (keep `showDeleteDialog`).

Replace the confirmation paragraph + Input inside the delete `<form>` (lines 68-79) with:

```svelte
<p class="text-sm text-ink-2 mb-4">
	This will permanently delete your account, all your data, and cannot be undone. Enter your
	<strong class="text-ink">password</strong> to confirm.
</p>
<form method="POST" action="?/delete" use:enhance class="space-y-3">
	<Input name="current_password" type="password" placeholder="Your password" required />
```

(The closing `</form>` and the Cancel/Delete buttons below stay unchanged.)

- [ ] **Step 3: Run check + lint**

Run: `cd svelte-frontend && npm run check && npm run lint`
Expected: 0 errors. (`Input` is already imported; `deleteHandle` removed cleanly.)

- [ ] **Step 4: Update the E2E delete test**

In `svelte-frontend/e2e/settings.spec.ts`, replace the `data page shows export and delete options` test with one that exercises the dialog and a wrong password (safe — does not actually delete):

```ts
test('delete account dialog rejects a wrong password', async ({ page, authUser }) => {
	await page.goto('/settings/data');
	await expect(page.getByRole('heading', { name: 'Export your data' })).toBeVisible();
	await expect(page.getByRole('heading', { name: 'Danger zone' })).toBeVisible();

	await page.getByRole('button', { name: 'Delete account' }).click();
	await page.getByPlaceholder('Your password').fill('definitely-wrong-password');
	await page.getByRole('button', { name: 'Delete my account' }).click();

	// Backend returns 403 → action returns fail(), so we stay on /settings/data.
	await expect(page).toHaveURL(/\/settings\/data/);
});
```

- [ ] **Step 5: Run the E2E test**

Run: `cd svelte-frontend && npx playwright test settings.spec.ts -g "delete account dialog"`
Expected: PASS (stays on `/settings/data`, account not deleted).

- [ ] **Step 6: Commit**

```bash
git add svelte-frontend/src/routes/settings/data/+page.server.ts \
        svelte-frontend/src/routes/settings/data/+page.svelte \
        svelte-frontend/e2e/settings.spec.ts
git commit -m "feat: wire account deletion with password"
```

---

### Task A3: Avatar upload auto-submit

**Files:**
- Modify: `svelte-frontend/src/routes/settings/+page.svelte:28-38`

- [ ] **Step 1: Locate the avatar file input**

Open `svelte-frontend/src/routes/settings/+page.svelte`. The avatar form (action `?/avatar`, `enctype="multipart/form-data"`, `use:enhance`) contains a hidden `<input type="file" id="avatar-upload" name="avatar" ...>` and an "Upload photo" button that only triggers `.click()` on the input.

- [ ] **Step 2: Add onchange auto-submit to the file input**

Add this attribute to the `<input type="file" ...>` element:

```svelte
onchange={(e) => e.currentTarget.form?.requestSubmit()}
```

So selecting a file submits the enclosing form to the existing `?/avatar` action (no submit button needed).

- [ ] **Step 3: Run check + lint**

Run: `cd svelte-frontend && npm run check && npm run lint`
Expected: 0 errors.

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/src/routes/settings/+page.svelte
git commit -m "fix: submit avatar form on file select"
```

---

### Task A4: Reading progress (current_page) input

**Files:**
- Modify: `svelte-frontend/src/lib/components/shelf/ShelfBookCard.svelte`
- Modify: `svelte-frontend/src/routes/shelf/+page.svelte`
- Test: `svelte-frontend/e2e/shelf.spec.ts` (add test) — verify file exists first; if not, add the test to `settings.spec.ts`-style new file `e2e/shelf-progress.spec.ts`.

- [ ] **Step 1: Add `onProgressChange` prop and an input to ShelfBookCard**

In `svelte-frontend/src/lib/components/shelf/ShelfBookCard.svelte`, add to the `Props` interface (after `onStatusChange`):

```ts
	onProgressChange: (entryId: number, currentPage: number) => Promise<void>;
```

Add `onProgressChange` to the destructured props:

```ts
	let { entry, onDelete, onRate, onStatusChange, onProgressChange }: Props = $props();
```

Replace the READING block (lines 77-79):

```svelte
{#if entry.status === 'READING'}
	<ProgressBar current={entry.current_page} total={book.page_count} />
{/if}
```

with:

```svelte
{#if entry.status === 'READING'}
	<ProgressBar current={entry.current_page} total={book.page_count} />
	<div class="flex items-center gap-2 pt-1">
		<label class="text-xs text-muted" for="page-{entry.id}">Page</label>
		<input
			id="page-{entry.id}"
			type="number"
			min="0"
			max={book.page_count ?? undefined}
			value={entry.current_page ?? 0}
			data-testid="current-page-input"
			class="w-20 rounded-md border border-rule bg-surface px-2 py-1 text-xs text-ink"
			onchange={(e) => onProgressChange(entry.id, Number(e.currentTarget.value))}
		/>
	</div>
{/if}
```

- [ ] **Step 2: Add the handler in the shelf page**

In `svelte-frontend/src/routes/shelf/+page.svelte`, add this function next to `handleStatusChange` (it follows the same optimistic-update pattern):

```ts
async function handleProgressChange(entryId: number, currentPage: number) {
	const i = entries.findIndex((e) => e.id === entryId);
	if (i === -1) return;
	const prev = entries[i].current_page;
	entries[i] = { ...entries[i], current_page: currentPage };
	const { error } = await updateShelfEntry(fetch, entryId, { current_page: currentPage });
	if (error) {
		entries[i] = { ...entries[i], current_page: prev };
		toast.error('Failed to update progress');
	}
}
```

Then pass it to the card in the `{#each}` block:

```svelte
<ShelfBookCard
	{entry}
	onDelete={handleDelete}
	onRate={handleRate}
	onStatusChange={handleStatusChange}
	onProgressChange={handleProgressChange}
/>
```

- [ ] **Step 3: Run check + lint**

Run: `cd svelte-frontend && npm run check && npm run lint`
Expected: 0 errors. (`updateShelfEntry` and `toast` are already imported in the shelf page.)

- [ ] **Step 4: Confirm the E2E shelf spec filename**

Run: `ls svelte-frontend/e2e/`
Expected: note whether `shelf.spec.ts` exists. Use that file if present; otherwise create `svelte-frontend/e2e/shelf-progress.spec.ts` with the same `import { test, expect } from './fixtures';` header used by other specs.

- [ ] **Step 5: Add an E2E test for setting progress**

Add this test (in `shelf.spec.ts` if present, else the new file). It assumes a fixture that puts a book on the shelf with status READING; if the existing shelf spec has a helper/fixture for that, reuse it. Minimal version using the UI to set status first:

```ts
test('user can set reading progress', async ({ page, authUser }) => {
	// Precondition: at least one READING entry. Reuse existing shelf seeding if available;
	// otherwise add a book via /discover then set status to Reading on /shelf.
	await page.goto('/shelf?tab=reading');
	const input = page.getByTestId('current-page-input').first();
	if (await input.count()) {
		await input.fill('42');
		await input.blur();
		await expect(page.getByTestId('progress-bar').first()).toHaveAttribute('data-current', '42');
	}
});
```

> If the shelf E2E suite has an established seeding helper for shelf entries, prefer it over the UI-driven precondition and make the assertion unconditional. Match the existing suite's patterns.

- [ ] **Step 6: Run the E2E test**

Run: `cd svelte-frontend && npx playwright test -g "set reading progress"`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add svelte-frontend/src/lib/components/shelf/ShelfBookCard.svelte \
        svelte-frontend/src/routes/shelf/+page.svelte \
        svelte-frontend/e2e/
git commit -m "feat: edit reading progress on shelf"
```

---

## Group C — Type contracts

### Task C1: Trim `UserMe` and remove the dead email_verified block

**Files:**
- Modify: `svelte-frontend/src/lib/api/user.ts:3-13`
- Modify: `svelte-frontend/src/routes/settings/+page.svelte:71-75`

- [ ] **Step 1: Trim the `UserMe` interface**

In `svelte-frontend/src/lib/api/user.ts`, replace the interface with only the fields the backend returns and consumers use:

```ts
export interface UserMe {
	id: number;
	handle: string;
	display_name: string;
	email: string;
	bio: string | null;
	avatar_url: string | null;
}
```

(Removed: `email_verified`, `joined_at`, `followers_count`, `following_count`.)

- [ ] **Step 2: Remove the email_verified UI block**

In `svelte-frontend/src/routes/settings/+page.svelte`, delete the block (lines 71-75):

```svelte
{#if user?.email_verified}
	<p class="text-xs text-success">✓ Verified</p>
{:else}
	<p class="text-xs text-warning">Not verified. Check your inbox.</p>
{/if}
```

Leave the rest of the Email card (the input + "Change email" button) intact.

- [ ] **Step 3: Run check + lint**

Run: `cd svelte-frontend && npm run check && npm run lint`
Expected: 0 errors. The check will fail loudly if any other file still reads a removed field — if so, that usage is also dead; remove it and note it.

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/src/lib/api/user.ts svelte-frontend/src/routes/settings/+page.svelte
git commit -m "refactor: align UserMe type with backend"
```

---

### Task C3: Trim the public-profile `User` type

**Files:**
- Modify: `svelte-frontend/src/lib/types/user.ts`

- [ ] **Step 1: Trim the `User` interface to the public-profile contract**

In `svelte-frontend/src/lib/types/user.ts`, replace the `User` interface with the fields `UserProfileSerializer` returns and `u/[handle]/+page.svelte` consumes:

```ts
export interface User {
	handle: string;
	display_name: string;
	bio: string | null;
	avatar_url: string | null;
	member_since: string;
	profile_public: boolean;
}
```

(Removed: `id`, `email`, `email_verified`.)

- [ ] **Step 2: Resolve `UserId`**

Check `UserId` usage:

Run: `cd svelte-frontend && grep -rn "UserId" src/`
- If only declared in `lib/types/user.ts` (now unused after removing `id`), delete the `export type UserId = number;` line.
- If used elsewhere, leave it.

- [ ] **Step 3: Run check + lint**

Run: `cd svelte-frontend && npm run check && npm run lint`
Expected: 0 errors. (`__fixtures__/user.ts` still references removed fields but is deleted in Task B3 — if check runs before B3 and errors only there, proceed; B3 removes it. To avoid order coupling, you may run B3 immediately after this task.)

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/src/lib/types/user.ts
git commit -m "refactor: align public User type with backend"
```

---

## Group B — Dead code removal

### Task B1: Remove unused Zod schemas and the `zod` dependency

**Files:**
- Delete: `svelte-frontend/src/lib/schemas/settings.ts`, `svelte-frontend/src/lib/schemas/user.ts`
- Modify: `svelte-frontend/package.json`

- [ ] **Step 1: Confirm zero importers, then delete**

Run: `cd svelte-frontend && grep -rn "lib/schemas/\(settings\|user\)\|from '\$lib/schemas" src/`
Expected: no results (only the files themselves). Then:

```bash
rm svelte-frontend/src/lib/schemas/settings.ts svelte-frontend/src/lib/schemas/user.ts
# remove the schemas dir if now empty:
rmdir svelte-frontend/src/lib/schemas 2>/dev/null || true
```

- [ ] **Step 2: Confirm `zod` has no other users, then drop it**

Run: `cd svelte-frontend && grep -rn "from 'zod'\|require('zod')" src/`
Expected: no results. Then remove the `"zod"` line from `dependencies` in `svelte-frontend/package.json` and refresh the lockfile:

Run: `cd svelte-frontend && npm install`
Expected: `zod` removed from `package-lock.json`.

- [ ] **Step 3: Run check + lint**

Run: `cd svelte-frontend && npm run check && npm run lint`
Expected: 0 errors.

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/src/lib/schemas svelte-frontend/package.json svelte-frontend/package-lock.json
git commit -m "chore: remove unused zod schemas and dep"
```

---

### Task B2: Remove generated types file and gitignore it

**Files:**
- Delete: `svelte-frontend/src/lib/types/api.generated.ts`
- Modify: `svelte-frontend/.gitignore`

- [ ] **Step 1: Confirm zero importers, then delete the file**

Run: `cd svelte-frontend && grep -rn "api.generated" src/`
Expected: no results. Then:

```bash
rm svelte-frontend/src/lib/types/api.generated.ts
```

- [ ] **Step 2: Gitignore the generated artifact**

Append to `svelte-frontend/.gitignore`:

```
# generated by `npm run types:api`, not committed
src/lib/types/api.generated.ts
```

- [ ] **Step 3: Run check + lint**

Run: `cd svelte-frontend && npm run check && npm run lint`
Expected: 0 errors. (The `types:api` script is unchanged and can still regenerate the file locally.)

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/src/lib/types/api.generated.ts svelte-frontend/.gitignore
git commit -m "chore: drop committed generated api types"
```

---

### Task B3: Remove the dev mock route and fixtures

**Files:**
- Delete: `svelte-frontend/src/routes/api/__mock/` (directory)
- Delete: `svelte-frontend/src/lib/api/__fixtures__/` (directory)

- [ ] **Step 1: Confirm the mock is not referenced**

Run: `cd svelte-frontend && grep -rn "__mock\|__fixtures__\|fixtureUser\|fixtureBooks" src/ e2e/`
Expected: references only inside the dirs being deleted. (E2E seeds via the real API, not fixtures — confirm no E2E hit appears.)

- [ ] **Step 2: Delete the directories**

```bash
rm -rf svelte-frontend/src/routes/api/__mock
rm -rf svelte-frontend/src/lib/api/__fixtures__
```

- [ ] **Step 3: Run check + lint**

Run: `cd svelte-frontend && npm run check && npm run lint`
Expected: 0 errors.

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/src/routes/api svelte-frontend/src/lib/api
git commit -m "chore: remove dev mock route and fixtures"
```

---

### Task B4: Remove dead `BookPreviewSerializer` (backend)

**Files:**
- Modify: `backend-django/books/serializers.py` (remove `BookPreviewSerializer`, lines ~10-21)

- [ ] **Step 1: Confirm it is unreferenced**

Run: `cd backend-django && grep -rn "BookPreviewSerializer" .`
Expected: only its own definition (no imports/usages in views, urls, tests).

- [ ] **Step 2: Delete the class**

Remove the `class BookPreviewSerializer(...)` block from `backend-django/books/serializers.py`. If it leaves an unused import at the top of the file, remove that too (ruff will flag it).

- [ ] **Step 3: Lint + Django check + tests**

Run: `cd backend-django && uv run ruff check . && uv run python manage.py check && DJANGO_ENV=dev uv run python manage.py test books`
Expected: ruff clean, system check OK, books tests pass.

- [ ] **Step 4: Commit**

```bash
git add backend-django/books/serializers.py
git commit -m "chore: remove unused BookPreviewSerializer"
```

---

### Task B5: Remove the no-op navbar Search button

**Files:**
- Modify: `svelte-frontend/src/lib/components/shell/AppShell.svelte`

- [ ] **Step 1: Remove the Search button**

In `svelte-frontend/src/lib/components/shell/AppShell.svelte`, delete the Search `<Button>`:

```svelte
<Button variant="ghost" size="icon" aria-label="Search">
	<Search class="size-5" />
</Button>
```

Then remove the now-unused import `import { Search } from 'lucide-svelte';` (line 4). The wrapping `<div class="flex items-center gap-2">` keeps `<UserMenu {user} />`.

- [ ] **Step 2: Run check + lint**

Run: `cd svelte-frontend && npm run check && npm run lint`
Expected: 0 errors (no unused `Search` import).

- [ ] **Step 3: Commit**

```bash
git add svelte-frontend/src/lib/components/shell/AppShell.svelte
git commit -m "chore: remove no-op navbar search button"
```

---

## Final verification gate

- [ ] **Step 1: Full frontend gates**

Run: `cd svelte-frontend && npm run check && npm run lint && npm run build`
Expected: 0 errors; production build succeeds.

- [ ] **Step 2: Full backend gates**

Run: `cd backend-django && uv run ruff check . && DJANGO_ENV=dev uv run python manage.py test`
Expected: ruff clean; all tests pass.

- [ ] **Step 3: Full E2E suite**

Run: `cd svelte-frontend && npx playwright test`
Expected: all specs pass (export download, delete-rejected, settings nav, shelf progress).

- [ ] **Step 4: Final dead-code sweep**

Run: `cd svelte-frontend && grep -rn "email_verified\|followers_count\|following_count\|joined_at\|__mock\|__fixtures__\|api.generated\|from 'zod'" src/ e2e/`
Expected: no results.

---

## Self-Review notes (already applied)
- Spec coverage: A1 export, A2 delete, A3 avatar, A4 current_page, B1–B5 dead code (schemas+zod, api.generated, mock+fixtures, BookPreviewSerializer, Search), C1 UserMe + email_verified block, C3 User type → all have tasks.
- Type consistency: `onProgressChange(entryId: number, currentPage: number)` used identically in ShelfBookCard (Task A4 Step 1) and shelf page (Step 2). `UserMe` trimmed fields match the removed `email_verified` UI usage (C1). `User` trimmed fields match public-profile consumption verified in spec C3.
- Ordering: deletions (B) run after type edits (C) because `__fixtures__` references the old `User` shape; Final gate re-runs everything.
