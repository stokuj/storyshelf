# App layout and wiki sidebar Implementation Plan (#89)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** SPA frame: sidebar with wiki Pages grouped by type, one URL per Page Path, universe view listing its books, characters and places.

**Architecture:** Pure helpers in `src/wiki.ts` (URL↔Path, grouping, universe membership) tested on the #88 fixtures. Root route renders a grid `Sidebar | <main><Outlet/></main>`. One splat route `routes/$.tsx` resolves any Page Path; universes get an extra member list.

**Tech Stack:** React 19, TanStack Router (file routes) + Query, Tailwind v4 + shadcn CSS variables, Vitest + Testing Library (jsdom), Fontsource.

**Spec:** `docs/superpowers/specs/2026-10-04-89-app-layout-sidebar.md`

## Global Constraints

- Colors: paper `#FCFBF8`, sidebar `#F6F3EE`, ink `#26201B`, muted `#6E665E`, accent `#B5502A`
- Fonts: Newsreader (headings), Public Sans (UI), via `@fontsource-variable/*`; drop `@fontsource-variable/geist`
- URL `/books/x` ↔ Path `/books/x.md`
- UI labels in English (like the mockups)
- `.dark` block untouched
- All commands run from `frontend/`; `make verify` from repo root before PR
- Commit titles ≤ 50 chars, conventional commits, no `Co-Authored-By`

## Review Focus

1. Unknown Path in URL (`/books/nope`) → "Page not found." inside the frame, sidebar still visible — test in Task 3
2. Same title twice (two "Geralt z Rivii") → disambiguated by the book title subtitle — test in Task 3 (sidebar link name includes book)
3. Universe must not leak pages from books outside it (Solaris) — test in Task 1 and Task 3
4. Brand link to `/` must not be marked active on every page (`aria-current` only on the current Page) — `activeOptions={{ exact: true }}` in Task 3, test asserts a single `aria-current` link
5. Character whose `book` has no Page → subtitle falls back to the raw path instead of crashing — covered by `titles.get(p.book) ?? p.book`, no fixture for it (OKF tolerates broken links)

---

### Task 1: Wiki helpers

**Files:**
- Create: `frontend/src/wiki.ts`
- Test: `frontend/src/wiki.test.ts`

**Interfaces:**
- Consumes: `listPages(): Page[]` from `src/api/store.ts`; `Page`, `PageType` from `src/api/types.ts`
- Produces:
  - `pageSplat(path: string): string` — `'/books/x.md'` → `'books/x'`
  - `pagePath(splat: string): string` — `'books/x'` → `'/books/x.md'`
  - `groupByType(pages: Page[]): Record<PageType, Page[]>`
  - `universeMembers(pages: Page[], universe: string): { books: Page[]; characters: Page[]; places: Page[] }`

- [ ] **Step 1: Write the failing test** (`src/wiki.test.ts`)

```ts
import { listPages } from '@/api/store'
import { groupByType, pagePath, pageSplat, universeMembers } from '@/wiki'

const pages = listPages()

test('groupByType puts every page in its type group', () => {
  const groups = groupByType(pages)
  expect(groups.book).toHaveLength(3)
  expect(groups.character).toHaveLength(8)
  expect(groups.place).toHaveLength(3)
  expect(groups.universe).toHaveLength(1)
})

test('universeMembers resolves characters and places through their book', () => {
  const m = universeMembers(pages, '/universes/wiedzmin.md')
  expect(m.books.map((p) => p.path).sort()).toEqual([
    '/books/krew-elfow.md',
    '/books/ostatnie-zyczenie.md',
  ])
  expect(m.characters).toHaveLength(5)
  expect(m.places).toHaveLength(2)
  const all = [...m.books, ...m.characters, ...m.places]
  expect(all.some((p) => p.path.includes('solaris'))).toBe(false)
})

test('pagePath reverses pageSplat', () => {
  expect(pageSplat('/books/krew-elfow.md')).toBe('books/krew-elfow')
  for (const p of pages) expect(pagePath(pageSplat(p.path))).toBe(p.path)
})
```

- [ ] **Step 2: Run, expect FAIL** — `npx vitest run src/wiki.test.ts` → cannot resolve `@/wiki`

- [ ] **Step 3: Implement** (`src/wiki.ts`)

```ts
// Pure helpers over wiki Pages: URL ↔ Path, grouping, universe membership
import type { Page, PageType } from './api/types'

// Path '/books/x.md' ↔ splat 'books/x' (URL '/books/x')
export const pageSplat = (path: string) => path.slice(1).replace(/\.md$/, '')
export const pagePath = (splat: string) => `/${splat}.md`

export function groupByType(pages: Page[]): Record<PageType, Page[]> {
  const groups: Record<PageType, Page[]> = { book: [], character: [], place: [], universe: [] }
  for (const p of pages) groups[p.type].push(p)
  return groups
}

// Characters and places belong to a universe through their book (CONTEXT: per book for now)
export function universeMembers(pages: Page[], universe: string) {
  const books = pages.filter((p) => p.type === 'book' && p.universe === universe)
  const bookPaths = new Set(books.map((b) => b.path))
  const inBooks = (type: PageType) =>
    pages.filter((p) => p.type === type && p.book !== null && bookPaths.has(p.book))
  return { books, characters: inBooks('character'), places: inBooks('place') }
}
```

- [ ] **Step 4: Run, expect PASS** — `npx vitest run src/wiki.test.ts`

- [ ] **Step 5: Commit** — `git add src/wiki.ts src/wiki.test.ts && git commit -m "feat: wiki grouping and universe helpers [#89]"`

---

### Task 2: Design tokens and fonts

**Files:**
- Modify: `frontend/package.json` (deps), `frontend/src/index.css`

- [ ] **Step 1: Swap fonts** — `npm uninstall @fontsource-variable/geist && npm install @fontsource-variable/newsreader @fontsource-variable/public-sans`

- [ ] **Step 2: Edit `src/index.css`**
  - Replace `@import '@fontsource-variable/geist';` with
    ```css
    @import '@fontsource-variable/newsreader';
    @import '@fontsource-variable/public-sans';
    ```
  - In `@theme inline`:
    ```css
    --font-heading: 'Newsreader Variable', serif;
    --font-sans: 'Public Sans Variable', sans-serif;
    ```
  - In `:root`: `--background`, `--card`, `--popover` → `#fcfbf8`; `--sidebar` → `#f6f3ee`; `--foreground`, `--card-foreground`, `--popover-foreground`, `--secondary-foreground`, `--accent-foreground`, `--sidebar-foreground`, `--sidebar-accent-foreground` → `#26201b`; `--muted-foreground` → `#6e665e`; `--primary`, `--sidebar-primary` → `#b5502a`. Everything else unchanged.

- [ ] **Step 3: Verify** — `npm run build` succeeds; `grep -c geist src/index.css package.json` → 0

- [ ] **Step 4: Commit** — `git add package.json package-lock.json src/index.css && git commit -m "feat: paper palette and Newsreader fonts [#89]"`

---

### Task 3: Layout, sidebar and page routes

**Files:**
- Create: `frontend/src/components/Sidebar.tsx`, `frontend/src/routes/$.tsx`, `frontend/src/test/renderApp.tsx`, `frontend/src/test/app.test.tsx`
- Modify: `frontend/src/routes/__root.tsx`, `frontend/src/routes/index.tsx`, `frontend/src/routeTree.gen.ts` (regenerated by the Vite plugin)
- Delete: `frontend/src/test/home.test.tsx` (replaced by `app.test.tsx`)

**Interfaces:**
- Consumes: Task 1 helpers; `usePages()`, `usePage(path)` from `src/api/hooks.ts`
- Produces: `renderApp(url?: string): Router` test helper

- [ ] **Step 1: Test helper** (`src/test/renderApp.tsx`)

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider, createMemoryHistory, createRouter } from '@tanstack/react-router'
import { render } from '@testing-library/react'
import { routeTree } from '@/routeTree.gen'

// Full app (all file routes) on an in-memory URL
export function renderApp(url = '/') {
  const router = createRouter({ routeTree, history: createMemoryHistory({ initialEntries: [url] }) })
  render(
    <QueryClientProvider client={new QueryClient()}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
  return router
}
```

- [ ] **Step 2: Write the failing tests** (`src/test/app.test.tsx`; delete `home.test.tsx`)

```tsx
import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { renderApp } from './renderApp'

const section = (root: HTMLElement, name: string) =>
  within(root).getByRole('heading', { name }).closest('section')!

test('home shows the sidebar and an empty state', async () => {
  renderApp('/')
  await screen.findByText('Pick a page from the sidebar.')
  screen.getByRole('navigation', { name: 'Wiki' })
})

test('sidebar lists every page grouped by type', async () => {
  renderApp('/')
  const nav = await screen.findByRole('navigation', { name: 'Wiki' })
  await within(nav).findByRole('link', { name: 'Solaris' })
  for (const [label, count] of [['Books', 3], ['Characters', 8], ['Places', 3], ['Universes', 1]] as const) {
    expect(within(section(nav, `${label} ${count}`)).getAllByRole('link')).toHaveLength(count)
  }
  // Same character in two books is told apart by the book title
  within(nav).getByRole('link', { name: 'Geralt z Rivii Krew elfów' })
  within(nav).getByRole('link', { name: 'Geralt z Rivii Ostatnie życzenie' })
})

test('clicking a page opens its path and highlights only it', async () => {
  const router = renderApp('/')
  fireEvent.click(await screen.findByRole('link', { name: 'Krew elfów' }))
  await waitFor(() => expect(router.state.location.pathname).toBe('/books/krew-elfow'))
  await screen.findByRole('heading', { level: 1, name: 'Krew elfów' })
  const current = document.querySelectorAll('[aria-current="page"]')
  expect(current).toHaveLength(1)
  expect(current[0].textContent).toBe('Krew elfów')
})

test('universe page lists its books, characters and places', async () => {
  renderApp('/universes/wiedzmin')
  const main = screen.getByRole('main')
  await within(main).findByRole('heading', { name: 'Books in this universe' })
  expect(within(section(main, 'Books in this universe')).getAllByRole('link')).toHaveLength(2)
  expect(within(section(main, 'Characters in this universe')).getAllByRole('link')).toHaveLength(5)
  expect(within(section(main, 'Places in this universe')).getAllByRole('link')).toHaveLength(2)
  expect(within(main).queryByText(/Solaris/)).toBeNull()
})

test('unknown path shows not found inside the frame', async () => {
  renderApp('/books/nope')
  await screen.findByText('Page not found.')
  screen.getByRole('navigation', { name: 'Wiki' })
})
```

- [ ] **Step 3: Run, expect FAIL** — `npx vitest run src/test/app.test.tsx` → no navigation / empty state

- [ ] **Step 4: Sidebar** (`src/components/Sidebar.tsx`)

```tsx
import { Link } from '@tanstack/react-router'
import { usePages } from '@/api/hooks'
import type { PageType } from '@/api/types'
import { groupByType, pageSplat } from '@/wiki'

const SECTIONS: [PageType, string][] = [
  ['book', 'Books'],
  ['character', 'Characters'],
  ['place', 'Places'],
  ['universe', 'Universes'],
]

export function Sidebar() {
  const { data: pages = [] } = usePages()
  const groups = groupByType(pages)
  const titles = new Map(pages.map((p) => [p.path, p.title]))

  return (
    <nav aria-label="Wiki" className="flex flex-col gap-6 overflow-y-auto border-r bg-sidebar p-4">
      <Link to="/" activeOptions={{ exact: true }} className="px-2 font-heading text-xl font-semibold">
        Storyshelf
      </Link>
      {SECTIONS.map(([type, label]) => (
        <section key={type}>
          <h2 className="mb-1 flex justify-between px-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
            {label} <span>{groups[type].length}</span>
          </h2>
          <ul>
            {groups[type].map((p) => (
              <li key={p.path}>
                <Link
                  to="/$"
                  params={{ _splat: pageSplat(p.path) }}
                  className="block rounded-md px-2 py-1 text-sm hover:bg-background"
                  activeProps={{ className: 'bg-background font-medium text-primary' }}
                >
                  {p.title}
                  {p.book && (
                    <span className="block text-xs font-normal text-muted-foreground">
                      {titles.get(p.book) ?? p.book}
                    </span>
                  )}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </nav>
  )
}
```

- [ ] **Step 5: Root layout** (`src/routes/__root.tsx`)

```tsx
import { Outlet, createRootRoute } from '@tanstack/react-router'
import { Sidebar } from '@/components/Sidebar'

export const Route = createRootRoute({
  component: RootLayout,
})

function RootLayout() {
  return (
    <div className="grid h-svh grid-cols-[16rem_1fr]">
      <Sidebar />
      <main className="overflow-y-auto px-12 py-10">
        <Outlet />
      </main>
    </div>
  )
}
```

- [ ] **Step 6: Empty state** (`src/routes/index.tsx`)

```tsx
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/')({
  component: HomePage,
})

function HomePage() {
  return <p className="text-muted-foreground">Pick a page from the sidebar.</p>
}
```

- [ ] **Step 7: Page route** (`src/routes/$.tsx`)

```tsx
import { Link, createFileRoute } from '@tanstack/react-router'
import { usePage, usePages } from '@/api/hooks'
import type { Page } from '@/api/types'
import { pagePath, pageSplat, universeMembers } from '@/wiki'

export const Route = createFileRoute('/$')({
  component: PageRoute,
})

function PageRoute() {
  const { _splat = '' } = Route.useParams()
  const { data: page, isError } = usePage(pagePath(_splat))
  if (isError) return <p className="text-muted-foreground">Page not found.</p>
  if (!page) return null

  // ponytail: title + Path only; #90 renders the body below
  return (
    <article>
      <p className="font-mono text-xs text-muted-foreground">{page.path}</p>
      <h1 className="mt-1 font-heading text-4xl">{page.title}</h1>
      {page.type === 'universe' && <UniverseMembers universe={page.path} />}
    </article>
  )
}

function UniverseMembers({ universe }: { universe: string }) {
  const { data: pages = [] } = usePages()
  const { books, characters, places } = universeMembers(pages, universe)
  const titles = new Map(pages.map((p) => [p.path, p.title]))
  return (
    <>
      <PageList title="Books in this universe" pages={books} titles={titles} />
      <PageList title="Characters in this universe" pages={characters} titles={titles} />
      <PageList title="Places in this universe" pages={places} titles={titles} />
    </>
  )
}

function PageList({ title, pages, titles }: { title: string; pages: Page[]; titles: Map<string, string> }) {
  if (pages.length === 0) return null
  return (
    <section className="mt-8">
      <h2 className="font-heading text-xl">{title}</h2>
      <ul className="mt-3 flex flex-wrap gap-2">
        {pages.map((p) => (
          <li key={p.path}>
            <Link
              to="/$"
              params={{ _splat: pageSplat(p.path) }}
              className="block rounded-md border px-3 py-1 text-sm hover:text-primary"
            >
              {p.title}
              {p.book && <span className="ml-2 text-muted-foreground">{titles.get(p.book) ?? p.book}</span>}
            </Link>
          </li>
        ))}
      </ul>
    </section>
  )
}
```

- [ ] **Step 8: Regenerate route tree and run tests** — `npm run build` (plugin rewrites `routeTree.gen.ts`), then `npm run test` → all PASS

- [ ] **Step 9: Full frontend gate** — `npm run typecheck && npm run lint && npm run format:check` (run `npm run format` if needed)

- [ ] **Step 10: Commit** — `git add -A src && git commit -m "feat: app layout, wiki sidebar and page routes [#89]"`

---

### Task 4: Verify

- [ ] `make verify` from repo root → green
- [ ] Dev stack + `npm run dev`; screenshots of `/`, `/books/ostatnie-zyczenie`, `/universes/wiedzmin`
