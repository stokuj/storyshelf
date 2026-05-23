# 11 — Polish pass

After all functional slices land, do one full pass on quality:

1. **Empty states** for every list: catalog, shelves, reviews, characters,
   relations, activity, chats. Always: friendly copy + an icon + a CTA.
2. **Error boundaries**: `+error.svelte` at the root, plus one in `/books/[slug]`
   and `/u/[handle]`. Each has retry + go-home buttons.
3. **404**: `src/routes/+error.svelte` handles 404 with a literary line.
4. **Keyboard nav**:
   - All routes reachable without a mouse.
   - Tabs / dropdowns / dialogs trap focus correctly.
   - Visible focus ring on every interactive element.
   - Skip-to-main-content link.
5. **a11y**:
   - All images have alt; decorative icons have `aria-hidden="true"`.
   - Color contrast WCAG AA. Re-run with `axe`.
   - The relation graph has a sibling `<ul>` for screen readers.
6. **Performance**:
   - `<img loading="lazy">` on covers below the fold.
   - Code-split `@xyflow/svelte` — only load on book detail.
   - `prerender = true` on legal pages, login, signup.
7. **Meta**:
   - `<svelte:head>` per route with proper title + description.
   - Open Graph tags on book and profile pages.
   - `manifest.webmanifest` for installability.
8. **Lint/test**:
   - `pnpm check` zero errors.
   - `pnpm lint` zero warnings.
   - At least one Playwright test for the AI Cast Panel happy path.

## Acceptance

- Lighthouse mobile: Performance ≥ 85, A11y ≥ 95, Best Practices ≥ 95.
- A keyboard-only walkthrough of Discover → Book → AI panel → Verify → Profile → Settings works.
