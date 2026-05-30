# 04 — Discover route

Read `docs/handoff/04-routes-and-screens.md` → "Discover".

Implement `/discover`:

1. **Route**:
   - `src/routes/discover/+page.server.ts` — `load()` parses search params
     (`q`, `genre`, `sort`, `page`) and calls `listBooks(fetch, params)`.
   - `+page.svelte` reads `data.books` and renders the page.
   - URL is the source of truth — filters write back via `goto`.
2. **Components**:
   - `book/BookGrid.svelte` — responsive grid (5 / 3 / 2 cols), props: `books`.
   - `book/BookGridSkeleton.svelte` — 10 skeletons.
   - `discover/FilterBar.svelte` — genre dropdown, sort dropdown, character
     combobox. Emits via two-way `bind:value` against URL-driven state.
   - `discover/ContainsCharacterCombobox.svelte` — `Command` based combobox
     that calls `searchByCharacter(name)` on each keystroke (debounced 250ms),
     shows results, and on select sets `?character=`.
3. **Behavior**:
   - "Load more" pagination — append next page on click.
   - Empty state component when zero results.
   - Use `<svelte:head>` to set title `"Discover — Storyshelf"`.

## Acceptance

- `/discover` renders the fixture books in MOCK mode.
- Changing genre → URL updates → list refetches.
- Typing in the character combobox shows matching books.
- Page renders correctly at 320px / 768px / 1280px / 1920px widths.
- Keyboard: Tab order is logical; Enter on a card navigates to `/books/[slug]`.
- Visual reference: `docs/handoff/wireframes/Wireframes.html` (Variant A, sheet 01).
