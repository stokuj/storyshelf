# StoryShelf — SvelteKit Frontend

SvelteKit 2 + Svelte 5 + Tailwind v4 frontend for StoryShelf.

## Dev setup

```bash
npm install
cp .env.example .env
npm run types:api   # generate API types from ../docs/api/openapi.yml
npm run dev         # http://localhost:5174
```

## Commands

| Command             | Description                        |
| ------------------- | ---------------------------------- |
| `npm run dev`       | Start dev server on :5174          |
| `npm run check`     | svelte-check + TypeScript          |
| `npm run lint`      | ESLint + Prettier check            |
| `npm run format`    | Format with Prettier               |
| `npm run build`     | Production build (Node adapter)    |
| `npm run types:api` | Regenerate types from OpenAPI spec |
| `npm test`          | Run Vitest                         |

## Architecture

See `../svelte(wideframe)/handoff/` for the full frontend implementation plan (Phases 2.7–2.9).
See `../docs/ARCHITECTURE.md` for system overview.
