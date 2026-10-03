# Spec — scaffold React + Vite SPA (#87)

> Data: 2026-10-03 · Issue: #87 · Milestone: M1 · Decyzje: ADR-002, ADR-005

## Cel

Pusty, działający frontend w `frontend/`: `npm run dev` pokazuje placeholder, CI ma zielony job `frontend`.

## Decyzje

| Temat | Decyzja | Powód |
|---|---|---|
| Menedżer pakietów | npm (`package-lock.json` w repo) | prosto, zgodnie z issue |
| Node | CI: Node 24 (Active LTS); `engines.node: ">=22.12"`; `.nvmrc` = `24` | wymóg Vite 8: `^20.19 \|\| >=22.12` |
| TypeScript | **6.0.x (`~6.0.3`), nie 7.0** | typescript-eslint 8.71 ma peer `typescript <6.1.0`; TS 7.0 nie ma jeszcze API programowego. Upgrade, gdy typescript-eslint wspiera TS 7.1 |
| Routing | TanStack Router, routing plikowy (`@tanstack/router-plugin/vite`) | domyślna ścieżka w docs |
| `routeTree.gen.ts` | commitowany, wyłączony z ESLint i Prettier | `tsc` w CI działa bez wcześniejszego `vite build` |
| Dane | TanStack Query: `QueryClientProvider` w `main.tsx` | — |
| Styl | Tailwind v4 przez `@tailwindcss/vite` + `shadcn init` (`components.json`, `src/lib/utils.ts` z `cn()`, zmienne CSS) | bez komponentów, dojdą przy makietach |
| Alias | `@/` → `src/` (tsconfig + vite) | wymagany przez shadcn |
| Lint/format | ESLint 10 flat config: `@eslint/js`, `typescript-eslint` (recommended, bez type-checked), `react-hooks`, `react-refresh`, `eslint-config-prettier`; Prettier z domyślnym configiem | standard z szablonu Vite |
| Testy | Vitest 5 + jsdom + Testing Library + jest-dom; jeden smoke test placeholdera | dowód, że pipeline testów działa |
| Dev | Vite na hoście, proxy `/api` → `http://localhost:8000` | ADR-002 same-origin; bez kontenera Node |
| Devtools | brak | YAGNI, dodać przy pierwszych zapytaniach |

## Wersje (npm registry, 2026-10-03)

react / react-dom 19.3 · vite 8.3 · @vitejs/plugin-react 6.1 · typescript 6.0.3 · tailwindcss / @tailwindcss/vite 4.3 · @tanstack/react-router 1.170 · @tanstack/router-plugin 1.168 · @tanstack/react-query 5.104 · eslint 10.12 · typescript-eslint 8.71 · eslint-plugin-react-hooks 7.1 · eslint-plugin-react-refresh 0.5 · prettier 3.9 · vitest 5.0 · jsdom 30 · @testing-library/react 16.3 · @testing-library/jest-dom 7.0 · shadcn 4.21

Instalujemy przez `npm install <pkg>@latest` (z wyjątkiem `typescript@~6.0.3`), żeby lock odzwierciedlał najnowsze wersje.

## Skrypty `frontend/package.json`

| Skrypt | Komenda |
|---|---|
| `dev` | `vite` |
| `build` | `tsc -b && vite build` |
| `typecheck` | `tsc -b` |
| `lint` | `eslint .` |
| `format` / `format:check` | `prettier --write .` / `prettier --check .` |
| `test` | `vitest run` |

## Zmiany poza `frontend/`

- `.github/workflows/ci.yml`: job `frontend` (setup-node 24 z cache npm → `npm ci` → typecheck → lint → format:check → test → build). `build-and-push` bez zmian.
- `Makefile` `verify`: dopisane `npm run typecheck`, `lint`, `format:check`, `test` w `frontend/`.
- `.gitignore`: `frontend/dist/`.
- `CLAUDE.md`: komendy frontendu i `frontend/` w layoucie.

## Poza zakresem

- Serwowanie buildu przez Caddy w prod (osobne zadanie przy deployu SPA).
- Komponenty shadcn, layout aplikacji, klient API, auth.
- E2E Playwright.

## Kryteria akceptacji

1. `cd frontend && npm ci && npm run dev` → `http://localhost:5173/` pokazuje placeholder „StoryShelf”.
2. `npm run typecheck && npm run lint && npm run format:check && npm run test && npm run build` przechodzą lokalnie.
3. Request `/api/...` z dev servera trafia do Django na `:8000` (proxy).
4. Job `frontend` w CI zielony.
