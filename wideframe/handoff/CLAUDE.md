# Storyshelf — Claude Code instructions

This is the frontend repo for **Storyshelf** — a Goodreads-style book site with LLM
features that extract characters and their relations from books.

**Backend is already built.** Your job is the frontend only.
You implement **Variant A** from `docs/handoff/wireframes/` — classic catalog +
book page with an optional AI "Meet the cast" side panel.

---

## Stack — non-negotiable

- **SvelteKit 2** with **Svelte 5** runes only (`$state`, `$derived`, `$props`, `$effect`).
  - No Svelte 4 syntax. No `export let`. No `$:` reactive statements. No legacy stores
    unless data must cross routes.
- **TypeScript strict**.
- **Tailwind v4** (CSS-first config via `@theme` in `src/app.css` — **no `tailwind.config.js`**).
- **shadcn-svelte** for primitives. Install per-component:
  `npx shadcn-svelte@latest add button card dialog tabs avatar input label switch radio-group dropdown-menu sheet sonner tooltip badge separator skeleton`
- **bits-ui** (already a peer dep of shadcn-svelte) for any headless component shadcn doesn't cover.
- **lucide-svelte** for icons.
- **superforms** + **zod** for forms (settings page, reviews, etc.).
- **@xyflow/svelte** for relation graphs (used in the AI extraction modal and any
  optional Variant B experiments later).
- **mode-watcher** for dark mode.
- **clsx** + **tailwind-merge** (wrapped as `cn()` in `src/lib/utils.ts`).

**Do NOT** add: Inter font, Roboto, Fraunces, react-anything, styled-components,
emotion, MUI, Chakra, jQuery.

---

## Project conventions

### File layout
```
src/
  app.css                  # Tailwind v4 @theme block + global tokens
  app.html
  hooks.server.ts          # auth cookie passthrough
  lib/
    api/                   # typed wrappers around backend endpoints
      books.ts
      characters.ts
      user.ts
      ai.ts
    components/
      ui/                  # shadcn-svelte primitives (auto-generated)
      book/                # BookCard, BookGrid, BookHeader, ReviewItem, ...
      character/           # CharacterCard, CharacterAvatar, RelationBadge
      ai/                  # AICastPanel, AIExtractionModal, AIBadge
      shell/               # AppShell, NavBar, UserMenu, Search
    types.ts               # re-exports from src/lib/types/
    types/
      book.ts
      character.ts
      user.ts
      ai.ts
    utils.ts               # cn(), formatRating, formatDate, initials
    config.ts              # env-derived constants
  routes/
    +layout.svelte         # AppShell
    +layout.server.ts      # session
    +page.svelte           # home (redirect → /discover for logged-in)
    discover/+page.svelte
    books/[id]/+page.svelte
    books/[id]/+page.ts
    books/[id]/characters/[charId]/+page.svelte
    characters/+page.svelte
    u/[handle]/+page.svelte
    settings/+layout.svelte
    settings/+page.svelte                # account
    settings/profile/+page.svelte        # profile & privacy
    settings/notifications/+page.svelte
    settings/ai/+page.svelte
    settings/data/+page.svelte
    login/+page.svelte
    signup/+page.svelte
```

### Naming
- Components: `PascalCase.svelte`.
- Files in `lib/api/`, `lib/utils.ts`, `routes/**`: `kebab-case` or framework convention.
- Type names: `PascalCase`. Type files export the named type only — no default exports.

### Components
- Props via `$props()` with **destructured TS interfaces**, e.g.:
  ```svelte
  <script lang="ts">
    interface Props { book: Book; size?: 'sm' | 'md' | 'lg'; }
    let { book, size = 'md' }: Props = $props();
  </script>
  ```
- State via `$state()`. Derived values via `$derived()`. No `let count = 0` + manual reactivity.
- Side effects via `$effect()` — keep them minimal. Prefer derived.
- No prop drilling more than 2 levels — use Svelte 5 `setContext`/`getContext` or a runed module.

### Data flow
- **All** server data comes from `+page.server.ts` or `+page.ts` `load()` functions.
- **Never** call `fetch` directly inside `+page.svelte`. Always go through `src/lib/api/*.ts`.
- Mutations use form actions when possible. For AI calls or anything that needs live
  state, use a typed client wrapper that hits the same `+server.ts` route.
- Use SvelteKit's built-in `fetch` from `load` — never raw `window.fetch`.

### Styling
- Tailwind classes first. Drop to `<style>` only for things Tailwind can't express
  (custom keyframes, complex `:has()` rules, etc.).
- All colors, radii, font sizes, and spacing tokens come from `@theme` in `app.css`.
  Never hardcode hex.
- Dark mode: class-based (`class="dark"` on `<html>`). Configure via `mode-watcher`.

### Forms
- Always `superforms` + `zod`. Schemas live in `src/lib/schemas/`.
- Always client-side validation + server-side validation in actions.

### Errors
- Use `error()` from `@sveltejs/kit` in loaders. Always include a message.
- Render errors via `+error.svelte` per route group.
- Toasts: `sonner` (via shadcn-svelte).

### Accessibility
- Every interactive element keyboard-reachable. Visible focus rings (`focus-visible:ring-2`).
- All icons that aren't decorative have `aria-label`.
- The relation graph has a **keyboard-only fallback list** rendered next to it (already
  designed in the wireframe).

---

## Variant A — what we're building

See `docs/handoff/wireframes/Wireframes.html` (Variant A tab — already the default after
the latest revision) for screen-by-screen visuals. The five core screens:

1. **Discover** — book grid + search + filters (incl. "contains character …" AI filter).
2. **Book page** — 3-column: cover + CTA | description + reviews | **AI "Meet the cast"** side panel.
3. **Character page** — opened from the AI panel; bio, quotes, relations, also-appears-in.
4. **Profile** — classic shelves & activity + a dashed AI sidecar with extraction history.
5. **Settings** — account, profile visibility (public/friends/private), avatar, password.

See `04-routes-and-screens.md` for per-screen acceptance criteria.

---

## Style of work

- **One slice per turn.** Don't try to build the whole app in one shot.
- After each slice: `pnpm check`, `pnpm lint`, `pnpm build`. Fix every warning.
- When you're unsure about API shape or copy, **add a `TODO: clarify`** comment and stop.
- Commit messages: `feat(book-page): ai cast panel skeleton` style.
