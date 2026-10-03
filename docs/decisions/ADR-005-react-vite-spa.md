# ADR-005 — Frontend od zera: React + Vite SPA zamiast SvelteKit

> Status: Accepted · Data: 2026-10-03 · Kontekst: pivot na wiki (ADR-004)

## Decyzja

Po pivocie około 70% `svelte-frontend/` (books, discover, feed, shelf, stats, users) jest do usunięcia. Najpierw powstają makiety kluczowych ekranów w jaśniejszej wersji obecnego stylu. Potem `svelte-frontend/` jest usuwany w całości, a frontend powstaje od zera jako **Vite SPA**: React 19 + TypeScript + TanStack Router + TanStack Query + Tailwind v4 + shadcn/ui, a do renderu Stron react-markdown.

- **Bez SSR**: Wiki i Profil są prywatne, więc SEO nie ma znaczenia. Znika forwardowanie cookies w SSR (`handleFetch`), a frontend to pliki statyczne serwowane przez Caddy, bez kontenera Node w prod.
- **Next.js / React Router v7 (framework) odrzucone**: drugi serwer obok Django i dwa backendy. Wrócić do tego, jeśli publiczne Wiki będą potrzebować SEO.
- `/api` zostaje same-origin (ADR-002 w mocy). Czat z Agentem: streaming SSE z Django.
