# 05 — Book detail (no AI panel yet)

Read `docs/handoff/04-routes-and-screens.md` → "Book detail".

Implement `/books/[slug]` **without** the AI cast panel — that comes in prompt 06.

1. **Route**:
   - `+page.server.ts` loads `getBook(slug)` + `getReviews(slug, page=1)`.
   - `+page.svelte` renders the 3-column layout. Right column is **empty** for
     now (a placeholder `<div class="hidden lg:block" />`).
2. **Components**:
   - `book/BookHeader.svelte` — title, author, year, genres.
   - `book/BookActions.svelte` — `Want to read` split button with `DropdownMenu`
     for shelf choice. Optimistic UI: shelf change fires `addToShelf` and updates
     local state immediately, rolls back on error.
   - `book/BookDescription.svelte` — typography-tuned description block with
     `font-display italic`-style pulled quotes if the description has any.
   - `review/ReviewList.svelte`, `review/ReviewItem.svelte`, `review/ReviewComposer.svelte`.
     Composer uses **superforms** with a schema requiring 1..5 rating and 10..5000 char body.
   - `review/RatingStars.svelte` — interactive (read-only mode for display).
3. **Loading**: per-section skeletons; never block the whole route on reviews.

## Acceptance

- `/books/dune` renders all metadata, description, and review list.
- Writing a review posts to the form action, refetches, and toasts "Review posted".
- Errors from the API render inline (composer) or via toast (action buttons).
- Layout: 3 cols at ≥1024px, stacks at smaller widths.
- Visual reference: Variant A, sheet 02 (but with empty right column for now).
