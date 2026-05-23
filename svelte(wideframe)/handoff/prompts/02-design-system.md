# 02 — Design system, shell, atoms

Read `docs/handoff/01-design-system.md` again.

Implement:

1. **Fonts**: add the Newsreader + Public Sans `<link>` tags in `src/app.html`.
2. **`app.css`**: finish the full `@theme` block (colors, fonts, radii) and the
   `.dark` override. Add a single `@layer base` block setting body background,
   text color, font-family, and a thin selection color.
3. **`AppShell`**:
   - `src/lib/components/shell/AppShell.svelte` — top nav bar (brand, search command
     trigger, nav links: Discover / Characters / My shelf / AI, right-side user menu),
     and a `<slot />` for the page.
   - Sticky top nav with `bg-paper/80 backdrop-blur border-b border-rule`.
   - `Search` button opens the shadcn `Command` palette (`Cmd+K`).
4. **Atoms** under `src/lib/components/`:
   - `book/BookCover.svelte` — sized aspect-2/3 cover with fallback striped placeholder
     when `cover_url` is null. Props: `book`, `size` (`'xs' | 'sm' | 'md' | 'lg' | 'xl'`).
   - `book/BookCard.svelte` — cover + title + author + genre badge.
   - `character/CharacterAvatar.svelte` — circular, props: `character`, `size`. Falls
     back to monogram initials.
   - `character/RelationBadge.svelte` — colored dot + label, color picked by `kind`.
   - `ai/AIBadge.svelte` — `Sparkles` icon + "AI" pill in `bg-accent-soft text-accent-ink`.
   - `ai/AIPanel.svelte` — empty wrapper with dashed accent border + title slot.
5. **`UserMenu`** — avatar trigger, `DropdownMenu` with Profile / Settings / Sign out.
   For now, hardcode the user as `{ handle: 'demo', display_name: 'Demo User' }`.
6. **Dark mode toggle** in the user menu via `mode-watcher`.

## Acceptance

- Visit `/` (empty page) — top bar renders with brand, nav, search button, user menu.
- `Cmd+K` opens the command palette with a placeholder input.
- Toggling dark mode swaps colors instantly; no flash.
- Every atom has at least one snapshot test (`Vitest`).
- All components use `Props` interface destructured from `$props()`. No `export let`.

Do not create any pages yet.
