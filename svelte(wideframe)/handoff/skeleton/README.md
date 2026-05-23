# Skeleton files

Drop-in starter files for a fresh SvelteKit project. After
`pnpm dlx sv create . --types ts` runs, replace the generated
versions with these:

- `package.json` — pinned dependency set for the chosen stack.
  Run `pnpm install` after replacing.
- `app.css` — the full `@theme` block. Put it at `src/app.css`.
- `vite.config.ts` — wires the Tailwind v4 plugin alongside SvelteKit.

The `app.html` head section, ESLint config, and Prettier config are
left to claude-cli to generate during prompt `01-setup`.
