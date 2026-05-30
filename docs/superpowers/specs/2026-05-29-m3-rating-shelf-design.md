# M3 — Reading Statuses + Ratings — Design Spec

> **Status:** approved design, ready for `/writing-plans`.
> **Source of truth:** `docs/GOAL.md` (decisions #11–#33, #58). This spec consolidates the five
> previous phase plans (`2026-05-27-phase-3a..3e`) into one design, optimized for parallel
> subagent execution. The old phase plans are superseded and removed.

## Context

After PRE-M3-FIX the project is at a clean **M2-complete** state. The Django apps `ratings/` and
`shelf/` **do not exist** — M3 creates both from scratch. (The old phase plans assumed `shelf/`
already existed and only needed editing; that assumption is obsolete.)

Existing, relied-upon:
- `books.Book` with `slug`, `title`, `cover_url`, `page_count`, `avg_rating`, `ratings_count`,
  nested authors/genres (M2).
- JWT-cookie auth, SSR `apiFetch` + `serverApiBase()` (`INTERNAL_API_URL`) pattern.
- `svelte-frontend/src/lib/components/ui/` are hand-rolled stubs; **`ui/select` is broken** (renders
  without open/close state). M3 must not depend on it.

## Goal

A user can mark a reading status (Want to Read / Reading / Read), track page progress, and rate
books 1–5 stars. Ratings update the community average. Statuses and ratings are visible and editable
on a dedicated `/shelf` page and on the book detail page.

## Success criteria

- Rating a book updates `Book.avg_rating` + `ratings_count` atomically (signal).
- A book can be added to the shelf and its status/progress/rating changed from the UI.
- `/shelf` shows the user's books in three status tabs with inline status/rating/progress controls.
- `/books/[slug]` shows interactive rating + a shelf-status control.
- A logged-in user reaches their shelf via a **"Shelf"** link in the top navbar.
- Backend tests green; `npm run check`/`lint` clean; Playwright shelf E2E green; OpenAPI snapshot
  regenerated.

## Out of scope (M3)

- Reviews (M4), custom shelves / collections (M5).
- **Editing `start_date`/`finish_date` in the UI** — the fields exist in the model/API but no M3
  screen edits them.
- Rating distribution bars (M4, decisions #41/#48).
- Follow UI (post-MVP).

---

## 1. Data model

### `ratings/models.py` — `Rating`

```python
class Rating(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ratings")
    book = models.ForeignKey("books.Book", on_delete=models.CASCADE, related_name="ratings")
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "book"], name="unique_user_book_rating"),
        ]
```

### `ratings/signals.py` — community average

`post_save` and `post_delete` on `Rating` recompute the book's aggregates:

```python
@transaction.atomic
def recompute_book_rating(book_id: int) -> None:
    book = Book.objects.select_for_update().get(pk=book_id)
    agg = Rating.objects.filter(book_id=book_id).aggregate(avg=Avg("rating"), count=Count("id"))
    book.avg_rating = round(agg["avg"], 2) if agg["count"] else 0.0
    book.ratings_count = agg["count"]
    book.save(update_fields=["avg_rating", "ratings_count"])
```

- `Book.avg_rating` is a non-nullable `FloatField(default=0.0)`, so it is `0.0` (not null) when there are zero ratings.
- Connected in `RatingsConfig.ready()`.

### `shelf/models.py` — `ShelfEntry`

```python
class ShelfEntry(models.Model):
    class Status(models.TextChoices):
        WANT_TO_READ = "WANT_TO_READ", "Want to Read"
        READING = "READING", "Reading"
        READ = "READ", "Read"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shelf_entries")
    book = models.ForeignKey("books.Book", on_delete=models.CASCADE, related_name="shelf_entries")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.WANT_TO_READ)
    start_date = models.DateField(null=True, blank=True)
    finish_date = models.DateField(null=True, blank=True)
    current_page = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "book"], name="unique_user_book_shelf"),
        ]

    def clean(self):
        if self.current_page is not None and self.book.page_count and self.current_page > self.book.page_count:
            raise ValidationError({"current_page": "current_page cannot exceed book.page_count."})
        if self.start_date and self.finish_date and self.finish_date < self.start_date:
            raise ValidationError({"finish_date": "finish_date cannot be before start_date."})
```

- Dates are manual; **no auto-set** on status transitions (decisions #12, #23).
- Status transitions are unrestricted (decision #23).

---

## 2. API contracts

These contracts are the **interface that lets the parallel lanes proceed independently**. They are
frozen here so the frontend lane (C) can hand-write matching TS types and the shelf lane (B) can rely
on the `ratings.Rating` import without waiting for lane A.

### Ratings — `/api/ratings/`

| Method | URL | Auth | Request → Response |
|--------|-----|------|--------------------|
| GET | `/api/ratings/?book_slug=<slug>` | IsAuthenticated | **user-scoped** — returns the current user's rating(s): `[{ "id": int, "book_slug": str, "rating": 1..5 }]` (0 or 1 item with `book_slug` filter). Not paginated (`pagination_class = None`). |
| PUT | `/api/ratings/` | IsAuthenticated | body `{ "book_slug": str, "rating": 1..5 }` → `update_or_create(user, book)`. **201** on create, **200** on update. Unknown `book_slug` → **404**. Returns `{ "id": int, "book_slug": str, "rating": int }`. |
| DELETE | `/api/ratings/{id}/` | IsAuthenticated + owner | **204**. Signal recomputes `Book.avg_rating`/`ratings_count`. |

- PUT is the upsert (decision #18). In M3 the GET is user-scoped (the book detail page reads the
  user's own rating); the community average comes from `Book.avg_rating`. The public rating
  *distribution* (decision #48) is **M4** and will extend this endpoint then — not built in M3.
- `user_rating` on shelf entries comes inline via Subquery (decision #22), so `/shelf` needs no
  ratings GET.

### Shelf — `/api/shelf/entries/`

`user_rating` is a `Subquery` annotation pulling the request user's rating from `ratings.Rating`
(decision #22). Endpoint identified by `book_slug` in the POST body (decision #20), `id` in URL for
PATCH/DELETE.

| Method | URL | Auth | Request → Response |
|--------|-----|------|--------------------|
| GET | `/api/shelf/entries/` | IsAuthenticated | current user's entries, **no pagination** (decision #28). Optional `?book_slug=<slug>` filter returns the single entry for that book (0 or 1 item) — used by the book detail page to know the current status. |
| POST | `/api/shelf/entries/` | IsAuthenticated | body `{ "book_slug": str, "status"?: Status, "current_page"?: int }`. **201**. Duplicate (unique user+book) → **400**. |
| PATCH | `/api/shelf/entries/{id}/` | IsAuthenticated + owner | partial `{ status?, current_page?, start_date?, finish_date? }`. **200**. |
| DELETE | `/api/shelf/entries/{id}/` | IsAuthenticated + owner | **204** (decision #30). |

**Entry shape (GET/POST/PATCH response item):**

```json
{
  "id": 12,
  "status": "READING",
  "current_page": 120,
  "start_date": null,
  "finish_date": null,
  "user_rating": 4,
  "book": {
    "slug": "the-hobbit",
    "title": "The Hobbit",
    "cover_url": "https://...",
    "authors": ["J. R. R. Tolkien"],
    "genres": ["Fantasy"],
    "avg_rating": 4.2,
    "page_count": 310
  }
}
```

---

## 3. Frontend

All frontend files live under `svelte-frontend/`. During the parallel phase, lane C **hand-writes**
TS types matching the contracts above (it does not depend on generated `types:api`, which is
regenerated only in the integration phase).

### Types & API client
- `src/lib/types/shelf.ts` — `ShelfStatus = 'WANT_TO_READ' | 'READING' | 'READ'`, `ShelfBook`, `ShelfEntry`.
- `src/lib/api/ratings.ts` — `rateBook(fetch, { book_slug, rating })`, `listRatings(fetch, book_slug)`, `deleteRating(fetch, id)`.
- `src/lib/api/shelf.ts` — `listShelf(fetch)`, `addToShelf(fetch, { book_slug, status })`, `updateEntry(fetch, id, patch)`, `removeEntry(fetch, id)`.

### Components
- `RatingStars.svelte` — 1–5 stars. Props: `rating: number | null`, `onRate: (star) => Promise<void>`, `readonly?`, `size?: 'sm' | 'md'`. Interactive when not readonly.
- `StatusDropdown.svelte` — pick `WANT_TO_READ | READING | READ`. **Self-contained dropdown** (the fixed `dropdown-menu` pattern: context `open` state + click-outside + Escape). **Must not use `ui/select`** (broken).
- `ProgressBar.svelte` — `current_page / page_count` as a percentage bar; hidden when `page_count` is null.
- `ShelfBookCard.svelte` — composes cover/title (link to `/books/[slug]`) + `StatusDropdown` + `RatingStars` + `ProgressBar`, all inline (decision #24). Optimistic mutations with rollback on error.
- `ShelfControl.svelte` — on the book detail page: when no entry → an **"Add to shelf"** affordance that POSTs (default `WANT_TO_READ`); when an entry exists → `StatusDropdown` + a remove action. PATCH/DELETE on change.

### Routes
- `src/routes/shelf/+layout.server.ts` — **auth guard**; redirect to `/login` when no user (decision #29).
- `src/routes/shelf/+page.server.ts` — SSR `listShelf` (decision #27: one GET, client-side filter).
- `src/routes/shelf/+page.svelte` — three tabs (`Want to Read | Reading | Read`), client-side filter by status with `$derived`, tab counts, `?tab=` query sync, empty states (CTA → `/discover`). No pagination.
- `src/routes/books/[slug]/+page.server.ts` — when authenticated, also load the user's rating and shelf entry (parallel to book fetch).
- `src/routes/books/[slug]/+page.svelte` — add `RatingStars` (auth-conditional: interactive vs display-only, community avg as text) and `ShelfControl`.

### Navigation
- `src/lib/components/shell/AppShell.svelte` — add a **"Shelf"** nav link in the top navbar next to
  "Discover", rendered only when `user` is logged in (`{#if user}`). Do **not** add it to `UserMenu`.

---

## 4. Parallel execution structure

One plan, organized so independent lanes own **disjoint file sets**. All shared-file edits happen in
the sequential foundation group; the three lanes never touch the same file.

| Group | Mode | Files owned |
|-------|------|-------------|
| **0 — Foundation** | sequential | `ratings/` skeleton (`apps.py`, `models.py`, migration, `urls.py` stub) · `shelf/` skeleton (same) · `config/settings/base.py` (`INSTALLED_APPS`) · `config/urls.py` (include both app urls). Establishes the `ratings.Rating` import contract; migrations run after this group. |
| **A — Ratings backend** | parallel | `ratings/serializers.py`, `ratings/signals.py`, `ratings/apps.py` (`ready()`), `ratings/views.py`, `ratings/urls.py`, `ratings/tests/` |
| **B — Shelf backend** | parallel | `shelf/serializers.py` (incl. `user_rating` Subquery → `ratings.Rating`), `shelf/views.py`, `shelf/urls.py`, `shelf/tests/` |
| **C — Frontend** | parallel | `svelte-frontend/src/lib/{types,api,components}/...`, `routes/shelf/*`, `routes/books/[slug]/*`, `lib/components/shell/AppShell.svelte` |
| **D — Integration + E2E** | sequential | regenerate `docs/api/openapi.yml` + `npm run types:api` (reconcile with hand-written types), full backend test suite, frontend `check`/`lint`, Playwright `e2e/shelf-*.spec.ts` + `global-setup` seed, fix integration seams |

**Order:** Group 0 → (A ∥ B ∥ C) → Group D. Lanes A/B/C have no shared files, so they can run as
concurrent agents (separate worktrees or same tree) without merge conflicts.

---

## 5. Testing

### Backend — ratings (`ratings/tests/`)
- Model: unique(user, book); rating bounds 1–5.
- Signal: `avg_rating`/`ratings_count` correct after save, update, and delete; `avg_rating` is `None` at zero ratings; concurrency-safe path uses `select_for_update`.
- API: PUT create → **201**; PUT same pair → **200** (update); GET requires `book_slug` (**400** without); DELETE → **204** + recompute; auth required for PUT/DELETE.

### Backend — shelf (`shelf/tests/`)
- Model `clean()`: `current_page` > `page_count` rejected; `finish_date` < `start_date` rejected.
- Unique(user, book): duplicate POST → **400**.
- CRUD: POST default status `WANT_TO_READ`; PATCH status/current_page; DELETE → **204**.
- `user_rating` Subquery returns the requesting user's rating (and `null` when none).
- Auth required; cross-user isolation (user A cannot see/modify user B's entries).

### E2E — Playwright (`e2e/shelf-*.spec.ts`, seeded via `global-setup`)
1. `/shelf` redirects anonymous user to `/login`.
2. Add a book to the shelf from `/books/[slug]`; it appears in the correct tab.
3. Three tabs filter by status; counts update.
4. Change status inline on `/shelf`.
5. Rate a book; community average reflects it.
6. Update progress; progress bar reflects it.
7. Cross-user isolation: user A's shelf is not visible to user B.

---

## 6. Decision traceability

GOAL.md decisions covered: #12 (current_page nullable, validated, no auto-set), #13 (no
personal_rating on ShelfEntry), #14 (`ratings/` app, unique(user,book)), #15 (signal
select_for_update + atomic), #18 (PUT upsert 201/200), #19 (`/api/shelf/entries/`), #20 (book_slug in
body), #21 (nested book), #22 (`user_rating` Subquery), #23 (unrestricted transitions), #24 (inline
controls on card), #25 (RatingWidget on `/shelf` + `/books/[slug]`), #26 (logical phases 3a–3e, here
reorganized as parallel lanes), #27 (one GET + client filter), #28 (no pagination), #29 (auth guard
in `+layout.server.ts`), #30 (DELETE supported), #58 (Subquery `user_rating`, not client-side merge).

Resolved gaps not in GOAL.md: add-to-shelf entry point = `ShelfControl` on `/books/[slug]`;
navigation = auth-only "Shelf" link in the top navbar; `start_date`/`finish_date` kept in
model/API but not edited in M3 UI.
