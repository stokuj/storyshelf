# React + Vite SPA Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Empty, working React SPA in `frontend/` with a placeholder page, lint/format/test tooling and a green CI job (#87).

**Architecture:** Vite 8 SPA, no SSR. TanStack Router file-based routes (`src/routes/`), TanStack Query provider in `main.tsx`, Tailwind v4 via Vite plugin, shadcn initialised (no components). Dev server proxies `/api` to Django on `localhost:8000` (same-origin, ADR-002).

**Tech Stack:** React 19.3, Vite 8.3, TypeScript 6.0.3, Tailwind 4.3, TanStack Router 1.170 / Query 5.104, shadcn 4.21, ESLint 10 + typescript-eslint 8.71, Prettier 3.9, Vitest 5 + jsdom + Testing Library.

**Spec:** `docs/superpowers/specs/2026-10-03-react-vite-scaffold.md`

## Global Constraints

- Package manager: npm; commit `frontend/package-lock.json`.
- Install every dependency with `@latest`, **except** `typescript@~6.0.3` (typescript-eslint peer range is `>=4.8.4 <6.1.0`; TS 7 is NOT allowed).
- `engines.node`: `">=22.12"`; `frontend/.nvmrc`: `24`; CI uses Node 24.
- TS 6: do NOT use `baseUrl` (deprecated); alias via `paths` only: `"@/*": ["./src/*"]`.
- `src/routeTree.gen.ts` is committed and excluded from ESLint and Prettier.
- No devtools, no shadcn components, no API client (out of scope).
- Conventional commits, title ≤ 50 chars, NO `Co-Authored-By` line.
- All commands run from `frontend/` unless stated.

## Review Focus

- Fresh clone, `npm ci` then `npm run typecheck` before any `vite` run → must pass (routeTree.gen.ts committed).
- `npm run format:check` on CI must not flag generated/lock files (`routeTree.gen.ts`, `package-lock.json`, `dist/`) → covered by `.prettierignore`.
- Request to `/api/...` on the dev server → proxied to `http://localhost:8000` (checked manually in Task 1 Step 9 with curl).
- `@/` alias resolves in tsc, Vite and Vitest alike → the smoke test imports via `@/`.
- `npm run lint` must not lint `dist/` or `routeTree.gen.ts` → `globalIgnores` in Task 2.

---

### Task 1: Vite app with router, query, Tailwind, shadcn and smoke test

**Files:**
- Create: `frontend/package.json`, `frontend/.nvmrc`, `frontend/index.html`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/tsconfig.app.json`, `frontend/tsconfig.node.json`, `frontend/src/main.tsx`, `frontend/src/index.css`, `frontend/src/routes/__root.tsx`, `frontend/src/routes/index.tsx`, `frontend/src/routeTree.gen.ts` (generated), `frontend/src/test/setup.ts`, `frontend/src/routes/index.test.tsx`, `frontend/components.json` (by shadcn), `frontend/src/lib/utils.ts` (by shadcn)
- Modify: `.gitignore` (root)

**Interfaces:**
- Produces: npm scripts `dev`, `build`, `typecheck`, `test`; alias `@/` → `src/`; exported `Route` from `src/routes/index.tsx` with component `HomePage`.

- [ ] **Step 1: Create `frontend/package.json`**

```json
{
  "name": "storyshelf-frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "engines": { "node": ">=22.12" },
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "typecheck": "tsc -b",
    "test": "vitest run"
  }
}
```

And `frontend/.nvmrc` containing `24`.

- [ ] **Step 2: Install dependencies**

```bash
npm install react@latest react-dom@latest @tanstack/react-router@latest @tanstack/react-query@latest
npm install -D vite@latest @vitejs/plugin-react@latest typescript@~6.0.3 @types/react@latest @types/react-dom@latest @types/node@latest @tanstack/router-plugin@latest tailwindcss@latest @tailwindcss/vite@latest vitest@latest jsdom@latest @testing-library/react@latest @testing-library/jest-dom@latest
```

Expected: no ERESOLVE errors. If a peer conflict appears, report it — do not use `--force`/`--legacy-peer-deps`.

- [ ] **Step 3: Configs**

`frontend/tsconfig.json`:
```json
{
  "files": [],
  "references": [{ "path": "./tsconfig.app.json" }, { "path": "./tsconfig.node.json" }],
  "compilerOptions": {
    "paths": { "@/*": ["./src/*"] }
  }
}
```

`frontend/tsconfig.app.json`:
```json
{
  "compilerOptions": {
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.app.tsbuildinfo",
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "types": ["vite/client", "vitest/globals", "@testing-library/jest-dom"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "verbatimModuleSyntax": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["src"]
}
```

`frontend/tsconfig.node.json`:
```json
{
  "compilerOptions": {
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.node.tsbuildinfo",
    "target": "ES2023",
    "lib": ["ES2023"],
    "module": "ESNext",
    "types": ["node"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "verbatimModuleSyntax": true,
    "moduleDetection": "force",
    "noEmit": true,
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  },
  "include": ["vite.config.ts"]
}
```

`frontend/vite.config.ts`:
```ts
/// <reference types="vitest/config" />
import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import { tanstackRouter } from '@tanstack/router-plugin/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  // tanstackRouter must come before react()
  plugins: [tanstackRouter({ target: 'react', autoCodeSplitting: true }), react(), tailwindcss()],
  resolve: {
    alias: { '@': path.resolve(import.meta.dirname, './src') },
  },
  server: {
    // Same-origin API in dev (ADR-002)
    proxy: { '/api': 'http://localhost:8000' },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
  },
})
```

If `/// <reference types="vitest/config" />` does not type `test` with Vitest 5, check Vitest 5 docs (context7) for the current way and use it.

- [ ] **Step 4: App sources**

`frontend/index.html`:
```html
<!doctype html>
<html lang="pl">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>StoryShelf</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

`frontend/src/index.css`:
```css
@import 'tailwindcss';
```

`frontend/src/routes/__root.tsx`:
```tsx
import type { QueryClient } from '@tanstack/react-query'
import { Outlet, createRootRouteWithContext } from '@tanstack/react-router'

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  component: Outlet,
})
```

`frontend/src/routes/index.tsx`:
```tsx
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/')({
  component: HomePage,
})

export function HomePage() {
  return (
    <main className="flex min-h-svh items-center justify-center">
      <h1 className="text-3xl font-semibold">StoryShelf</h1>
    </main>
  )
}
```

`frontend/src/main.tsx`:
```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider, createRouter } from '@tanstack/react-router'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { routeTree } from './routeTree.gen'

const queryClient = new QueryClient()
const router = createRouter({ routeTree, context: { queryClient } })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
)
```

`frontend/src/test/setup.ts`:
```ts
import '@testing-library/jest-dom/vitest'
```

- [ ] **Step 5: Write the smoke test (fails until build generates nothing broken — run it)**

`frontend/src/routes/index.test.tsx`:
```tsx
import { render, screen } from '@testing-library/react'
import { HomePage } from '@/routes/index'

test('home page shows the app name', () => {
  render(<HomePage />)
  expect(screen.getByRole('heading', { name: 'StoryShelf' })).toBeInTheDocument()
})
```

Note: `index.test.tsx` lives in `src/routes/` — TanStack Router ignores files matching its default `routeFileIgnorePattern`? Verify: if the generator treats `index.test.tsx` as a route (check `routeTree.gen.ts` after Step 6), move the test to `src/test/home.test.tsx` instead and keep the import `@/routes/index`.

Run: `npm run test` → Expected: PASS (1 test).

- [ ] **Step 6: Generate the route tree and build**

Run: `npm run build` (the router plugin writes `src/routeTree.gen.ts` during the Vite step; if `tsc -b` fails first because the file is missing, run `npx vite build` once, then `npm run build`).
Expected: `dist/` produced, `src/routeTree.gen.ts` exists and contains only `/` route.

- [ ] **Step 7: shadcn init**

Run: `npx shadcn@latest init -t vite -b radix -y` (check `npx shadcn@latest init --help` first; pick base color neutral if prompted).
Expected: `components.json`, `src/lib/utils.ts` (`cn()`), `src/index.css` rewritten with `@import "tailwindcss"` + theme CSS variables; deps `clsx`, `tailwind-merge`, `class-variance-authority`, `tw-animate-css`, `lucide-react` added.
Then re-run: `npm run typecheck && npm run test && npm run build` → all PASS.

- [ ] **Step 8: Root `.gitignore`**

Add under the `# Node / frontend` section:
```
frontend/dist/
```

- [ ] **Step 9: Manual check of dev server + proxy**

Run `npm run dev` in background; then:
- `curl -s localhost:5173/ | grep -q 'id="root"'` → match
- `curl -s -o /dev/null -w '%{http_code}' localhost:5173/api/` → any code other than Vite's 404 page from the SPA (if Django is down expect `500`/`502` proxy error, which still proves the proxy is wired). Stop the dev server.

- [ ] **Step 10: Commit**

```bash
git add .gitignore frontend
git commit -m "feat: scaffold React + Vite SPA"
```

---

### Task 2: ESLint + Prettier

**Files:**
- Create: `frontend/eslint.config.js`, `frontend/.prettierrc.json`, `frontend/.prettierignore`
- Modify: `frontend/package.json` (scripts), any source files reformatted by Prettier

**Interfaces:**
- Consumes: Task 1 project.
- Produces: npm scripts `lint`, `format`, `format:check`.

- [ ] **Step 1: Install**

```bash
npm install -D eslint@latest @eslint/js@latest typescript-eslint@latest eslint-plugin-react-hooks@latest eslint-plugin-react-refresh@latest globals@latest eslint-config-prettier@latest prettier@latest
```

- [ ] **Step 2: `frontend/eslint.config.js`**

```js
import js from '@eslint/js'
import prettier from 'eslint-config-prettier'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'
import globals from 'globals'
import tseslint from 'typescript-eslint'

export default defineConfig([
  globalIgnores(['dist', 'src/routeTree.gen.ts']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: { globals: globals.browser },
  },
  prettier,
])
```

Check each plugin's README (installed version) for the exact flat-config export name (`reactHooks.configs.flat.recommended` vs `reactHooks.configs['recommended-latest']`, `reactRefresh.configs.vite`) and use what exists.
`routes/*.tsx` export `Route` + a component; if `react-refresh/only-export-components` flags them, add `allowExportNames: ['Route']` to that rule rather than disabling it.

- [ ] **Step 3: Prettier config**

`frontend/.prettierrc.json`:
```json
{
  "semi": false,
  "singleQuote": true,
  "printWidth": 100
}
```

`frontend/.prettierignore`:
```
dist
src/routeTree.gen.ts
package-lock.json
```

- [ ] **Step 4: Scripts** in `frontend/package.json`:

```json
"lint": "eslint .",
"format": "prettier --write .",
"format:check": "prettier --check ."
```

- [ ] **Step 5: Run**

`npm run format` then `npm run lint && npm run format:check && npm run typecheck && npm run test && npm run build` → all PASS, zero lint warnings.

- [ ] **Step 6: Commit**

```bash
git add frontend
git commit -m "chore: add ESLint and Prettier to frontend"
```

---

### Task 3: CI job, make verify, CLAUDE.md

**Files:**
- Modify: `.github/workflows/ci.yml`, `Makefile` (`verify` target), `CLAUDE.md`

**Interfaces:**
- Consumes: scripts `typecheck`, `lint`, `format:check`, `test`, `build` from Tasks 1–2.

- [ ] **Step 1: CI job** — add after `test` job in `.github/workflows/ci.yml`:

```yaml
  frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version-file: frontend/.nvmrc
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - run: npm ci
      - run: npm run typecheck
      - run: npm run lint
      - run: npm run format:check
      - run: npm run test
      - run: npm run build
```

Leave `build-and-push` unchanged.

- [ ] **Step 2: Makefile `verify`** — append to the recipe:

```make
	cd $(ROOT_DIR)frontend && npm run typecheck && npm run lint && npm run format:check && npm run test
```

- [ ] **Step 3: CLAUDE.md**

In `## Komendy`, after the backend section add:

````markdown
### Frontend (z `frontend/`, Node 24)

```bash
npm ci
npm run dev          # http://localhost:5173, proxy /api → :8000
npm run typecheck
npm run lint
npm run format       # / format:check
npm run test         # Vitest
npm run build
```
````

In `## Layout (skrót)` add line: `frontend/          React 19 + Vite SPA; TanStack Router (src/routes/) + Query, Tailwind v4, shadcn`.
In `## Co to jest` second paragraph, replace „stary frontend usunięty” with „`frontend/` to szkielet nowego SPA (#87)”.
In the `Konwencje stylu` bullet add: `, ESLint + Prettier (frontend)`.

- [ ] **Step 4: Verify**

Run from repo root: `cd frontend && npm ci && npm run typecheck && npm run lint && npm run format:check && npm run test && npm run build`. Validate YAML: `python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci.yml'))"`.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/ci.yml Makefile CLAUDE.md
git commit -m "ci: add frontend job and docs"
```
