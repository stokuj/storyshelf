# 06 · Iteration plan

Feed claude-cli one prompt at a time, in this order. Each prompt in `prompts/`
ends with **acceptance criteria** that you check before moving on.

```
01-setup.md            — SvelteKit + Tailwind v4 + shadcn-svelte + ESLint/Prettier
02-design-system.md    — tokens, fonts, layout shell, dark mode, common atoms
03-api-and-types.md    — types, zod schemas, lib/api wrappers, env wiring
04-discover.md         — /discover route with mocked then real data
05-book-detail.md      — /books/[slug] (no AI panel yet) + reviews
06-ai-cast-panel.md    — AI extraction panel: generate, verify, reject, refresh
07-character-pages.md  — in-book + cross-book character routes
08-profile.md          — /u/[handle] (respect visibility)
09-settings.md         — full /settings section with superforms
10-ai-chat.md          — Ask-about-this-book Sheet with SSE streaming
11-polish.md           — empty states, error boundaries, keyboard nav, a11y pass
```

## Rules

- After each prompt: run `pnpm check`, `pnpm lint`, and screenshot the route.
- Don't move to the next slice until current acceptance criteria pass.
- Drift in copy is fine — fix at the end in `11-polish.md`.
- If claude-cli starts inventing features not in the spec, paste the relevant
  `handoff/*.md` section + "stick to this".

## Branch strategy (suggestion)

- `main` — never broken.
- One branch per slice: `feat/setup`, `feat/discover`, `feat/ai-cast-panel`, …
- PR each, merge after a manual run-through.
