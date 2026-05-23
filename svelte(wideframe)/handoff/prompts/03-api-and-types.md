# 03 — Types, schemas, API wrappers

Read `docs/handoff/02-data-model.md` and `docs/handoff/03-api-contract.md`.

Implement:

1. **Types**: every file under `src/lib/types/` exactly as in `02-data-model.md`.
   Re-export from `src/lib/types.ts`.
2. **Zod schemas** under `src/lib/schemas/` mirroring the types. Use `z.infer` to keep
   sync — i.e. types are derived from schemas where possible.
3. **API client**: `src/lib/api/_client.ts` with `apiFetch<T>` exactly as in §wrappers
   of the API doc.
4. **Resource wrappers** — one file per resource:
   - `books.ts` — `listBooks`, `getBook`, `getReviews`, `createReview`, `searchByCharacter`.
   - `characters.ts` — `getBookCharacters`, `getBookRelations`, `getCharacter`,
     `getCharacterAppearances`, `updateCharacter`.
   - `user.ts` — `getMe`, `updateMe`, `changeEmail`, `changePassword`, `uploadAvatar`,
     `getUserSettings`, `updateUserSettings`, `getUser` (by handle), `getUserShelves`.
   - `ai.ts` — `runExtraction`, `getExtraction`, `refreshExtraction`,
     `verifyCharacter`, `verifyRelation`, `rejectCharacter`, `askAboutBook` (SSE).
   - `shelves.ts` — `getMyShelves`, `addToShelf`, `removeFromShelf`.
5. **Env wiring**: `src/lib/config.ts` exports `API_URL`. `.env.example` is in repo root.
6. **Mock backend** for dev:
   - Create `src/routes/api/__mock/[...rest]/+server.ts` that returns hand-written
     fixtures when `PUBLIC_API_URL` is unset OR equals `MOCK`.
   - Fixtures live in `src/lib/api/__fixtures__/`. Cover at least: 2 books, 8 characters
     for one of them, 6 relations, 1 user, 1 settings record, 1 extraction.
   - Allow easy switch via env: `PUBLIC_API_URL=MOCK` → mock; otherwise real backend.

## Acceptance

- `pnpm check` passes.
- Writing in a sandbox `+page.server.ts`: `const books = await listBooks(fetch)` —
  TypeScript autocompletes the shape and returns the fixture in MOCK mode.
- Schemas catch a malformed payload in unit tests.

Still no routes/UI work beyond §atoms from prompt 02.
