# 01 — Setup

Read `docs/handoff/CLAUDE.md` and `docs/handoff/01-design-system.md` first.

Then:

1. Scaffold a SvelteKit 2 project with TypeScript, ESLint, Prettier, Vitest, and Playwright:
   ```
   pnpm dlx sv create . --types ts --no-add-ons --no-install
   pnpm i
   ```
2. Add Tailwind v4 (CSS-first; **do not create `tailwind.config.js`**):
   ```
   pnpm add -D tailwindcss @tailwindcss/vite
   ```
   In `vite.config.ts` add `tailwindcss()` to plugins.
   In `src/app.css`, start with the `@theme` block from `docs/handoff/01-design-system.md`.
   Import `src/app.css` from `src/routes/+layout.svelte`.
3. Add shadcn-svelte:
   ```
   pnpm dlx shadcn-svelte@latest init
   pnpm dlx shadcn-svelte@latest add button card dialog tabs avatar input label switch radio-group dropdown-menu sheet sonner tooltip badge separator skeleton command popover
   ```
4. Add other deps:
   ```
   pnpm add lucide-svelte mode-watcher clsx tailwind-merge @xyflow/svelte
   pnpm add sveltekit-superforms zod
   ```
5. Create `src/lib/utils.ts` exporting `cn()` (clsx + tailwind-merge).
6. Create `src/lib/config.ts` reading `PUBLIC_API_URL` from `$env/static/public`.
7. Add `.env.example` with `PUBLIC_API_URL=http://localhost:3001`.
8. Set up `src/routes/+layout.svelte` with `<ModeWatcher />`, `<Toaster />`, and a
   minimal `<AppShell>` placeholder.
9. Wire ESLint and Prettier to be strict (no warnings = no commit).

## Acceptance

- `pnpm dev` → http://localhost:5173 renders an empty layout in the warm paper color.
- `pnpm check` passes with 0 errors.
- `pnpm lint` passes with 0 warnings.
- Toggling `document.documentElement.classList.toggle('dark')` flips colors correctly.
- shadcn `Button` renders with the project accent (not its default zinc).

Stop here. Do not implement any routes yet.
