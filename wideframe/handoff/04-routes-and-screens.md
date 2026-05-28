# 04 · Routes & screens

## Sitemap

```
/                                  → redirect to /discover
/discover                          Catalog (book grid)
/books/[slug]                      Book detail (3-column, AI side panel)
/books/[slug]/characters           Full cast list (linked from AI panel)
/books/[slug]/characters/[charId]  Character detail (in-book)
/characters/[slug]                 Cross-book character detail
/u/[handle]                        Profile (shelves + AI history)
/settings                          Account (default settings tab)
/settings/profile                  Profile & privacy
/settings/notifications            Notifications
/settings/ai                       AI preferences
/settings/data                     Data & export, danger zone
/login
/signup
```

## Per-screen specs

### Discover (`/discover`)

**Goal:** find books, including by "contains character".

- Top bar with title `Discover` + "1,248 titles" count.
- Filter row (right-aligned):
  - `Genre` dropdown (multi-select via shadcn `DropdownMenu` with checkboxes).
  - `Sort` dropdown (`rating` / `recent` / `popular`).
  - **`Sparkles` icon + "Contains character…" `Combobox`** — typing fires
    `GET /books/contains-character?name=`.
- Grid: 5 columns desktop, 3 tablet, 2 mobile. Card = cover, title, author, genre chip.
- Infinite scroll OR pagination — your call; default to "Load more" button (simpler).
- Loading: 10 `Skeleton` cards.
- Empty state: friendly copy + cross-link to popular shelves.

**Data:** `+page.ts` `load()` calls `listBooks()` with query params from URL.
Filters update the URL via `goto(`?${params}`, { keepFocus: true, noScroll: true })`.

### Book detail (`/books/[slug]`)

**Goal:** classic book page with optional AI cast extraction.

**Layout:** 3 columns — `[140px] [1fr] [260px]` desktop, stack on mobile.

**Left column**
- Book cover.
- "Want to read" `Button` with split `DropdownMenu` (`Currently reading`, `Read`, `Custom shelf…`).
- Average rating + count below cover.

**Middle column**
- Title (display font), author(s) link, year, genres as `Badge`s.
- Description.
- `Reviews` section with `Tabs` (`Latest`, `Top`, `Yours`). Compose form + list.

**Right column — AI "Meet the cast" panel**
- Default state: dashed accent border, big `Generate ✨` `Button`, explainer copy.
- Spoiler control: `Slider` "I'm at chapter ___" (default = whole book if marked read,
  else last known progress).
- After generation: list of character cards (avatar + name + role). "See all (n)" link.
- Quick-action chips below: `Open relation graph`, `Spoiler-safe summary`, `Ask about this book`.
- All AI-sourced cards have `<AIBadge>` and a context-menu `verify` / `reject`.

**Behavior**
- Load runs `getBook` + `getReviews`. The AI extraction is fetched **lazily** via a
  `+server.ts` proxy or directly — only after the user clicks Generate, unless
  `ai_extraction_status === 'ready'`, in which case load `getExtraction` upfront.
- "Open relation graph" opens a full-screen `Dialog` containing the `@xyflow/svelte` graph.

### Character detail (`/books/[slug]/characters/[charId]`)

- Header: avatar (xl), name (display), AKA, role, tags.
- Two-column body: left = bio + quotes, right = relations list + "Also appears in".
- Edit button (visible to moderators / book owners) opens a `Sheet` from the right.

### Cross-book character (`/characters/[slug]`)

- Same header pattern.
- "Appears in" grid of book covers (top 12 + show more).
- Recurring relations across books (count badge per relation).
- AI section: `Archetype`, `Similar characters` (by embedding), `Famous quotes`.
- "+ Follow" button (this is the user-followed character feature).

### Profile (`/u/[handle]`)

- Header: avatar (xl), display name, handle, joined date, follower counts, top 3 genres.
- Reading challenge progress bar (`X / Y books`).
- Recently read row (6 covers).
- Activity feed (`ActivityItem` cards).
- Right rail: dashed AI sidecar with extraction history (book + char count + when).
- Respect visibility: if `private`, show only the avatar + "private profile" message
  when viewer isn't owner.

### Settings

Settings is a layout-driven section. `/settings` uses `+layout.svelte` to render the
left rail (matches the wireframe). Each subroute is its own page.

**`/settings` — Account**
- Avatar block (drag-drop / upload / generate).
- `Display name`, `Username`, `Email` (+ verify badge if `email_verified`).
- Password change form (current / new / confirm) with strength meter (`zxcvbn` optional).
- 2FA toggle.

**`/settings/profile` — Profile & privacy**
- 3 big radio cards: `Public` / `Friends only` / `Private`.
- Granular toggles: real-name visibility, activity in feed, show followed characters,
  AI learning, search-engine indexing.

**`/settings/ai` — AI preferences**
- Tone (`scholarly` / `casual` / `concise`).
- Default spoiler limit (`current-chapter` / `whole-book` / `no-limit`).
- Cite quotes (`always` / `on-request` / `never`).
- Chat history retention (Slider: 7 / 30 / 90 days / forever).

**`/settings/data` — Data & export + danger zone**
- Export all data (button → `POST /users/me/export`, show `download_url`).
- Pause account.
- Delete account (red, confirmation dialog with typed handle).

All settings forms use **superforms**. Auto-save on blur (debounced 600ms) with a
toast confirmation. `Save changes` button still present as a fallback.

## Layout / chrome

- `+layout.svelte` renders `<NavBar>` and `<main class="container">`.
- `NavBar`: brand left, search command (`Cmd-K`), nav links (`Discover`, `Characters`,
  `My shelf`, `AI`), user menu right.
- Footer minimal: copyright, links, language switch.
