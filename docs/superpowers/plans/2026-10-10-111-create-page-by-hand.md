# Create a Page by Hand from a Template Implementation Plan (#111)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A User creates an empty Strona of any Typ (book, character, place, universe) from a Szablon through a form at `/new`, without the Agent. The backend builds the Ścieżka and the Szablon; the frontend only collects fields and shows errors.

**Architecture:** `createBook(c)` becomes `createPage(input: NewPage)` (one endpoint, one function) and `add.tsx` calls it with `type: 'book'`. A new route `routes/_app/new.tsx` holds a controlled form (`useState`, native radio/input/select). A tiny pure helper `previewPath` in `src/wiki.ts` shows the Ścieżka that will be created. The test helper `mockWikiApi` learns to create every Typ with backend-equal Ścieżki and Szablon headings.

**Tech Stack:** React 19, TanStack Router + Query v5, Tailwind v4, Vitest + Testing Library (no jest-dom; globals on). No backend changes.

**Spec:** `docs/superpowers/specs/2026-10-10-111-create-page-by-hand.md` · Mockup: `docs/mockups/new-page-form.html`

## Global Constraints

- No new dependencies, no form library, no shadcn components; no `localStorage` / `sessionStorage` (ADR-001)
- Backend contract: `POST /api/wiki/pages/` body `{ type, title, author?, year?, book?, universe? }`; 201 returns the Page; 400 is `{ field: [msg] }`; 409 is `{ detail }` ("Page already exists: …"); character and place require `book`
- Ścieżka rules (`backend-django/wiki/okf.py`): `/{dir}/{slug}.md`, dir = `books|characters|places|universes`; character and place use `{slug}--{book-slug}`
- Empty optional fields are omitted from the body (DRF `CharField` rejects `""`); `year` is sent as a number; fields foreign to the chosen Typ are never sent
- UI copy, verbatim: link `New page`, heading `New page`, fieldset legend `Type`, radios `Book` `Character` `Place` `Universe`, labels `Title` `Author` `Year` `Universe` `Book`, button `Create page`, empty-books hint `Add a book first`, preview `Path: /books/krew-elfow.md`
- After success: `refreshPage` (sidebar + Page) and navigate to `/$` with `pageSplat(page.path)`
- `routeTree.gen.ts` is generated and committed (GOTCHAS); Prettier only under `frontend/`
- Code and comments in English; all commands run from `frontend/` unless stated; `make verify ENV_FILE=../../../infra/.env` from the worktree root at the end
- Commit titles at most 50 chars, conventional commits, ending `[#111]`, no `Co-Authored-By`; one simple git command per call (worktree guard, `docs/GOTCHAS.md`)

## Review Focus

1. Character or place without a chosen book sends no request; with one the body carries `book` (a Postać must not be created without its book) — test in Task 4
2. Taken Ścieżka (409) shows the backend message in an alert, stays on `/new` and the button works again — test in Task 4
3. Fast double click on `Create page` creates one Strona — test in Task 4
4. Changing the Typ after typing does not leak fields of the previous Typ (e.g. `author` of a book into a universe) — test in Task 4
5. No books yet: Book select is disabled and says `Add a book first` — test in Task 4

---

### Task 0: Worktree setup

- [ ] **Step 1: Install dependencies**

Run: `npm ci`
Expected: completes without errors

- [ ] **Step 2: Baseline**

Run: `npm run test`
Expected: all existing tests PASS (note the count)

---

### Task 1: `mockWikiApi` creates every Typ

**Files:**
- Modify: `frontend/src/test/mockWikiApi.ts`
- Test: `frontend/src/test/mockWikiApi.test.ts` (append)

**Interfaces:**
- Consumes: `slugify` from `@/wiki`, `NewPage` is NOT used yet (Task 2), the body is cast locally
- Produces: `POST /api/wiki/pages/` in the in-memory server accepts `{ type, title, author?, year?, book?, universe? }` and behaves like `services.create_page`: Ścieżka `/{dir}/{slug}.md` (`{slug}--{book-slug}` for character/place), frontmatter `type`, `title`, then `book` or `author`/`year`/`universe` when given, `status: draft`, Szablon headings of the Typ; 400 `{book: [...]}` when a character/place has no book or an unknown one; 400 `{title: [...]}` for an empty slug; 409 `{detail: 'Page already exists: <path>'}` on a taken Ścieżka

- [ ] **Step 1: Write the failing tests**

Append to `frontend/src/test/mockWikiApi.test.ts` (reuse its existing imports; add `ApiError` if not yet imported):

```ts
const create = (body: unknown) =>
  api<{ path: string; content: string }>('/wiki/pages/', {
    method: 'POST',
    body: JSON.stringify(body),
  })

test('POST builds the backend Path and Template for a character', async () => {
  const page = await create({ type: 'character', title: 'Ciri', book: '/books/krew-elfow.md' })
  expect(page.path).toBe('/characters/ciri--krew-elfow.md')
  expect(page.content).toContain('book: "/books/krew-elfow.md"')
  expect(page.content).toContain('status: draft')
  expect(page.content).toContain('## Rola w książce')
})

test('POST of a universe has only the Template heading Opis', async () => {
  const page = await create({ type: 'universe', title: 'Ziemiomorze' })
  expect(page.path).toBe('/universes/ziemiomorze.md')
  expect(page.content).toContain('## Opis')
  expect(page.content).not.toContain('## Streszczenie')
})

test('POST on a taken Path is 409, a character without a book is 400', async () => {
  const taken = await create({ type: 'book', title: 'Solaris' }).catch((e: unknown) => e)
  expect((taken as ApiError).status).toBe(409)
  const noBook = await create({ type: 'place', title: 'Ithaka' }).catch((e: unknown) => e)
  expect((noBook as ApiError).status).toBe(400)
  expect((noBook as ApiError).body).toEqual({ book: ['This field is required.'] })
})
```

- [ ] **Step 2: Run to verify they fail**

Run: `npx vitest run src/test/mockWikiApi.test.ts`
Expected: FAIL (the handler builds only `/books/...` pages, ignores `type`)

- [ ] **Step 3: Implement**

In `frontend/src/test/mockWikiApi.ts`:

- change the import to `import type { PageSummary, PageType, PageVersion, VersionKind } from '@/api/types'` and `import { parsePage, slugify } from '@/wiki'` (`bookPath` is no longer used)
- replace the `BOOK_HEADINGS` block with:

```ts
// copies of okf.TEMPLATES / okf.DIRS (kept literal so the mock is an independent oracle)
const TEMPLATES: Record<PageType, string[]> = {
  book: ['Streszczenie', 'Postacie', 'Miejsca', 'Wątki i motywy'],
  character: ['Opis', 'Rola w książce', 'Powiązania'],
  place: ['Opis', 'Rola w książce'],
  universe: ['Opis'],
}
const DIRS: Record<PageType, string> = {
  book: 'books',
  character: 'characters',
  place: 'places',
  universe: 'universes',
}
```

- replace the creating part of the `rest === ''` branch (from `const title = body().title as string` to the `return json(201, ...)`) with:

```ts
        const { type, title, author, year, book, universe } = body() as {
          type: PageType
          title: string
          author?: string
          year?: number
          book?: string
          universe?: string
        }
        const slug = slugify(title)
        if (!slug) return json(400, { title: ['Title needs at least one letter or digit'] })
        const perBook = type === 'character' || type === 'place'
        if (perBook && !book) return json(400, { book: ['This field is required.'] })
        if (perBook && !db.has(book!)) return json(400, { book: [`No book page at ${book}`] })
        const suffix = perBook ? `--${book!.slice('/books/'.length, -'.md'.length)}` : ''
        const path = `/${DIRS[type]}/${slug}${suffix}.md`
        if (db.has(path)) return json(409, { detail: `Page already exists: ${path}` })
        const meta = {
          type,
          title,
          ...(perBook ? { book } : type === 'book' ? { author, year, universe } : {}),
          status: 'draft',
        }
        const yaml = Object.entries(meta)
          .filter(([, v]) => v !== undefined)
          .map(([k, v]) => `${k}: ${JSON.stringify(v)}`)
          .join('\n')
        const headings = TEMPLATES[type].map((h) => `## ${h}\n`).join('\n')
        write(path, `---\n${yaml}\n---\n\n${headings}`, 'created')
        return json(201, detail(path))
```

- [ ] **Step 4: Run to verify they pass**

Run: `npx vitest run src/test/mockWikiApi.test.ts src/test/add-book.test.tsx`
Expected: PASS (add-book still green: a book body gives `/books/lalka.md` with the book Szablon)

- [ ] **Step 5: Format and commit**

Run: `npm run format`
Run: `git add frontend/src/test/mockWikiApi.ts frontend/src/test/mockWikiApi.test.ts`
Run: `git commit -m "test: mock wiki API creates every page type [#111]"`

---

### Task 2: `createPage` replaces `createBook`

**Files:**
- Modify: `frontend/src/api/types.ts` (append)
- Modify: `frontend/src/api/wiki.ts`
- Modify: `frontend/src/api/hooks.ts`
- Modify: `frontend/src/routes/_app/add.tsx`
- Test: `frontend/src/test/add-book.test.tsx` (regression, unchanged)

**Interfaces:**
- Consumes: nothing new
- Produces: `NewPage` (`@/api/types`); `createPage(input: NewPage): Promise<Page>` (`@/api/wiki`); `useCreatePage()` (`@/api/hooks`) whose `mutate(input: NewPage)` resolves to the created `Page`

This is a rename refactor: the existing `add-book.test.tsx` (it asserts the exact POST body `{type:'book', title, author, year}`) is the safety net, green before and after.

- [ ] **Step 1: Baseline**

Run: `npx vitest run src/test/add-book.test.tsx`
Expected: PASS

- [ ] **Step 2: Implement**

Append to `frontend/src/api/types.ts` (after `Candidate`):

```ts
// POST /api/wiki/pages/ body; the server picks the Path and the Template
export interface NewPage {
  type: PageType
  title: string
  author?: string
  year?: number
  book?: string // Path of the book, required for character and place
  universe?: string // Path of the universe, book only
}
```

In `frontend/src/api/wiki.ts`: change the type import to `import type { NewPage, Page, PageSummary, PageType, PageVersion, Paginated } from './types'` (drop `Candidate`) and replace `createBook` with:

```ts
export const createPage = (input: NewPage) =>
  api<Page>('/wiki/pages/', { method: 'POST', body: JSON.stringify(input) })
```

In `frontend/src/api/hooks.ts`: import `createPage` instead of `createBook`; change `import type { Candidate, PageType }` to `import type { NewPage, PageType }`; replace `useCreateBook` with:

```ts
export function useCreatePage() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (input: NewPage) => createPage(input),
    onSuccess: (page) => refreshPage(qc, page.path),
  })
}
```

In `frontend/src/routes/_app/add.tsx`: `useCreateBook` → `useCreatePage` in the import and in `CandidateCard`, and the call becomes:

```ts
            create.mutate(
              { type: 'book', title: c.title, author: c.author, year: c.year },
              {
                onSuccess: (page) =>
                  navigate({ to: '/$', params: { _splat: pageSplat(page.path) } }),
                onError: () => (started.current = false),
              },
            )
```

- [ ] **Step 3: Verify**

Run: `npm run typecheck`
Run: `grep -rn "createBook\|useCreateBook" src`
Run: `npx vitest run src/test/add-book.test.tsx`
Expected: typecheck clean, grep prints nothing, tests PASS

- [ ] **Step 4: Format and commit**

Run: `npm run format`
Run: `git add frontend/src/api/types.ts frontend/src/api/wiki.ts frontend/src/api/hooks.ts frontend/src/routes/_app/add.tsx`
Run: `git commit -m "refactor: createPage replaces createBook [#111]"`

---

### Task 3: `previewPath` helper

**Files:**
- Modify: `frontend/src/wiki.ts` (after `bookPath`)
- Test: `frontend/src/wiki.test.ts` (append; reuse its imports and add `previewPath`)

**Interfaces:**
- Consumes: `slugify`, `pageSplat` (same file)
- Produces: `previewPath(type: PageType, title: string, book: string): string | null` — the Ścieżka the backend will build (`/books/krew-elfow.md`, `/characters/geralt--ostatnie-zyczenie.md`), or `null` while it cannot be known (empty slug; character/place without `book`)

- [ ] **Step 1: Write the failing test**

```ts
test.each([
  ['book', 'Krew elfów', '', '/books/krew-elfow.md'],
  ['universe', 'Wiedźmin', '', '/universes/wiedzmin.md'],
  ['character', 'Geralt', '/books/ostatnie-zyczenie.md', '/characters/geralt--ostatnie-zyczenie.md'],
  ['place', 'Kaer Morhen', '/books/krew-elfow.md', '/places/kaer-morhen--krew-elfow.md'],
  ['character', 'Geralt', '', null],
  ['book', '  !!  ', '', null],
] as const)('previewPath %s %j %j', (type, title, book, expected) => {
  expect(previewPath(type, title, book)).toBe(expected)
})
```

- [ ] **Step 2: Run to verify it fails**

Run: `npx vitest run src/wiki.test.ts`
Expected: FAIL (`previewPath is not a function`)

- [ ] **Step 3: Implement**

In `frontend/src/wiki.ts` after `bookPath`:

```ts
const DIRS: Record<PageType, string> = {
  book: 'books',
  character: 'characters',
  place: 'places',
  universe: 'universes',
}

// Path the backend will build for a new Page (okf.page_path); null while unknown
export function previewPath(type: PageType, title: string, book: string): string | null {
  const slug = slugify(title)
  if (!slug) return null
  if (type !== 'character' && type !== 'place') return `/${DIRS[type]}/${slug}.md`
  return book ? `/${DIRS[type]}/${slug}--${pageSplat(book).replace(/^books\//, '')}.md` : null
}
```

- [ ] **Step 4: Run to verify it passes**

Run: `npx vitest run src/wiki.test.ts`
Expected: PASS

- [ ] **Step 5: Format and commit**

Run: `npm run format`
Run: `git add frontend/src/wiki.ts frontend/src/wiki.test.ts`
Run: `git commit -m "feat: previewPath for new pages [#111]"`

---

### Task 4: `/new` form and sidebar link

**Files:**
- Create: `frontend/src/routes/_app/new.tsx`
- Modify: `frontend/src/components/Sidebar.tsx` (link under "Add book")
- Modify: `frontend/src/routeTree.gen.ts` (generated)
- Test: `frontend/src/test/new-page.test.tsx` (create)

**Interfaces:**
- Consumes: `useCreatePage`, `usePages` (`@/api/hooks`); `apiErrorMessage` (`@/api/client`); `NewPage`, `PageType`; `previewPath`, `pageSplat` (`@/wiki`)
- Produces: route `/_app/new`; sidebar link `New page` to `/new`

- [ ] **Step 1: Write the failing tests**

`frontend/src/test/new-page.test.tsx` (accessible names: radios are `role=radio`, selects `combobox`, so `Book` radio and `Book` select do not clash; optional fields are matched by prefix because their label contains "optional"):

```tsx
import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { json } from './mockFetch'
import { mockWikiApi } from './mockWikiApi'
import { renderApp } from './renderApp'

const fill = (name: string | RegExp, value: string) =>
  fireEvent.change(screen.getByRole('textbox', { name }), { target: { value } })
const pick = (name: string, value: string) =>
  fireEvent.change(screen.getByRole('combobox', { name }), { target: { value } })
const submit = () => fireEvent.click(screen.getByRole('button', { name: 'Create page' }))
const posts = () => vi.mocked(fetch).mock.calls.filter(([, init]) => init?.method === 'POST')
const postBody = () => JSON.parse(posts()[0][1]!.body as string) as unknown

async function openForm() {
  const router = renderApp('/')
  fireEvent.click(await screen.findByRole('link', { name: 'New page' }))
  await screen.findByRole('heading', { level: 1, name: 'New page' })
  return router
}

test('a book from the form opens as an empty draft Template listed in the sidebar', async () => {
  const router = await openForm()
  expect(router.state.location.pathname).toBe('/new')
  fill('Title', 'Krew elfów')
  screen.getByText('/books/krew-elfow.md')
  submit()
  await waitFor(() => expect(router.state.location.pathname).toBe('/books/krew-elfow'))
  const main = screen.getByRole('main')
  await within(main).findByRole('heading', { level: 1, name: 'Krew elfów' })
  within(main).getByRole('heading', { name: 'Wątki i motywy' })
  within(main).getByText('draft')
})

test('a character needs a book; with one the body carries it', async () => {
  const router = renderApp('/new')
  fireEvent.click(await screen.findByRole('radio', { name: 'Character' }))
  fill('Title', 'Ciri')
  const button = screen.getByRole('button', { name: 'Create page' }) as HTMLButtonElement
  expect(button.disabled).toBe(true)
  submit()
  expect(posts()).toHaveLength(0)
  await screen.findByRole('option', { name: 'Solaris' })
  pick('Book', '/books/krew-elfow.md')
  screen.getByText('/characters/ciri--krew-elfow.md')
  submit()
  await waitFor(() =>
    expect(router.state.location.pathname).toBe('/characters/ciri--krew-elfow'),
  )
  expect(postBody()).toEqual({ type: 'character', title: 'Ciri', book: '/books/krew-elfow.md' })
})

test('empty Author and Universe are omitted, Year is a number', async () => {
  const router = renderApp('/new')
  fill('Title', 'Lalka')
  fill(/^Year/, '1890')
  submit()
  await waitFor(() => expect(router.state.location.pathname).toBe('/books/lalka'))
  expect(postBody()).toEqual({ type: 'book', title: 'Lalka', year: 1890 })
})

test('switching the type does not send fields of the previous type', async () => {
  const router = renderApp('/new')
  fill('Title', 'Ziemiomorze')
  fill(/^Author/, 'Ursula Le Guin')
  fireEvent.click(await screen.findByRole('radio', { name: 'Universe' }))
  submit()
  await waitFor(() => expect(router.state.location.pathname).toBe('/universes/ziemiomorze'))
  expect(postBody()).toEqual({ type: 'universe', title: 'Ziemiomorze' })
})

test('a taken Path shows the backend message and stays on the form', async () => {
  const router = renderApp('/new')
  fill('Title', 'Solaris')
  submit()
  const alert = await screen.findByRole('alert')
  expect(alert.textContent).toBe('Page already exists: /books/solaris.md')
  expect(router.state.location.pathname).toBe('/new')
  expect((screen.getByRole('button', { name: 'Create page' }) as HTMLButtonElement).disabled).toBe(
    false,
  )
})

test('a double click creates the page once', async () => {
  const router = renderApp('/new')
  fill('Title', 'Lalka')
  submit()
  submit()
  await waitFor(() => expect(router.state.location.pathname).toBe('/books/lalka'))
  expect(posts()).toHaveLength(1)
})

test('without books the Book list is disabled and says why', async () => {
  mockWikiApi({ 'GET /api/wiki/pages/?type=book': () => json(200, []) })
  renderApp('/new')
  fireEvent.click(await screen.findByRole('radio', { name: 'Place' }))
  await screen.findByRole('option', { name: 'Add a book first' })
  expect((screen.getByRole('combobox', { name: 'Book' }) as HTMLSelectElement).disabled).toBe(true)
})
```

Note: `setup.ts` installs `mockWikiApi()` for every test (as `add-book.test.tsx` relies on); only the last test calls it again, before `renderApp`, to pass an override.

- [ ] **Step 2: Run to verify they fail**

Run: `npx vitest run src/test/new-page.test.tsx`
Expected: FAIL (no `New page` link; `/new` not found)

- [ ] **Step 3: Implement the sidebar link**

In `frontend/src/components/Sidebar.tsx`, right after the `Add book` `<Link>`:

```tsx
      <Link
        to="/new"
        className="rounded-md border px-2 py-1 text-center text-sm hover:bg-background"
        activeProps={{ className: 'bg-background text-primary' }}
      >
        New page
      </Link>
```

- [ ] **Step 4: Implement the route**

`frontend/src/routes/_app/new.tsx`:

```tsx
// New page: pick a Type, fill the Template fields, create an empty Page (no Agent)
import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { apiErrorMessage } from '@/api/client'
import { useCreatePage, usePages } from '@/api/hooks'
import type { NewPage, PageType } from '@/api/types'
import { pageSplat, previewPath } from '@/wiki'

export const Route = createFileRoute('/_app/new')({
  component: NewPageForm,
})

const TYPES: [PageType, string][] = [
  ['book', 'Book'],
  ['character', 'Character'],
  ['place', 'Place'],
  ['universe', 'Universe'],
]

const field = 'flex flex-col gap-1.5 text-sm font-semibold'
const control = 'rounded-md border bg-background px-3 py-1.5 font-normal'
const optional = <span className="text-xs font-normal text-muted-foreground">optional</span>

function NewPageForm() {
  const [type, setType] = useState<PageType>('book')
  const [title, setTitle] = useState('')
  const [author, setAuthor] = useState('')
  const [year, setYear] = useState('')
  const [universe, setUniverse] = useState('')
  const [book, setBook] = useState('')
  const books = usePages('book').data ?? []
  const universes = usePages('universe').data ?? []
  const create = useCreatePage()
  const navigate = useNavigate()
  // isPending updates after re-render, so a fast double click would start a second create
  const started = useRef(false)
  const needsBook = type === 'character' || type === 'place'
  const ready = title.trim() !== '' && (!needsBook || book !== '')
  const preview = previewPath(type, title, book)

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!ready || started.current) return
    started.current = true
    // undefined fields are dropped by JSON.stringify, so only the chosen Type's fields are sent
    const input: NewPage = {
      type,
      title: title.trim(),
      author: type === 'book' ? author.trim() || undefined : undefined,
      year: type === 'book' && year ? Number(year) : undefined,
      universe: type === 'book' ? universe || undefined : undefined,
      book: needsBook ? book : undefined,
    }
    create.mutate(input, {
      onSuccess: (page) => navigate({ to: '/$', params: { _splat: pageSplat(page.path) } }),
      onError: () => (started.current = false),
    })
  }

  return (
    <section className="max-w-xl">
      <h1 className="font-heading text-3xl">New page</h1>
      <p className="mt-1 text-muted-foreground">
        Start an empty page from a template. You fill it in yourself.
      </p>

      <form onSubmit={onSubmit} className="mt-6 flex flex-col gap-4 rounded-lg border p-6">
        <fieldset className="flex flex-col gap-2">
          <legend className="mb-2 text-sm font-semibold">Type</legend>
          <div className="grid grid-cols-4 gap-1.5 rounded-md bg-muted p-1">
            {TYPES.map(([value, label]) => (
              <label
                key={value}
                className="rounded-md py-1.5 text-center text-sm has-checked:bg-background has-checked:font-semibold has-checked:text-primary"
              >
                <input
                  type="radio"
                  name="type"
                  checked={type === value}
                  onChange={() => setType(value)}
                  className="sr-only"
                />
                {label}
              </label>
            ))}
          </div>
        </fieldset>

        <label className={field}>
          Title
          <input value={title} onChange={(e) => setTitle(e.target.value)} className={control} />
        </label>

        {type === 'book' && (
          <>
            <div className="grid grid-cols-[2fr_1fr] gap-3">
              <label className={field}>
                Author {optional}
                <input
                  value={author}
                  onChange={(e) => setAuthor(e.target.value)}
                  className={control}
                />
              </label>
              <label className={field}>
                Year {optional}
                <input
                  type="number"
                  value={year}
                  onChange={(e) => setYear(e.target.value)}
                  className={control}
                />
              </label>
            </div>
            <label className={field}>
              Universe {optional}
              <select
                value={universe}
                onChange={(e) => setUniverse(e.target.value)}
                className={control}
              >
                <option value="">None</option>
                {universes.map((u) => (
                  <option key={u.path} value={u.path}>
                    {u.title}
                  </option>
                ))}
              </select>
            </label>
          </>
        )}

        {needsBook && (
          <label className={field}>
            Book
            <select
              value={book}
              onChange={(e) => setBook(e.target.value)}
              disabled={books.length === 0}
              className={control}
            >
              <option value="">{books.length ? 'Choose a book…' : 'Add a book first'}</option>
              {books.map((b) => (
                <option key={b.path} value={b.path}>
                  {b.title}
                </option>
              ))}
            </select>
          </label>
        )}

        {preview && (
          <p className="text-sm text-muted-foreground">
            Path: <code>{preview}</code>
          </p>
        )}

        {create.error && (
          <p role="alert" className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {apiErrorMessage(create.error)}
          </p>
        )}

        <button
          type="submit"
          disabled={!ready || create.isPending}
          className="w-fit rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:opacity-50"
        >
          Create page
        </button>
      </form>
    </section>
  )
}
```

- [ ] **Step 5: Regenerate the route tree and run the tests**

Run: `npm run build`
Expected: succeeds; `src/routeTree.gen.ts` now contains `/_app/new`
Run: `npx vitest run src/test/new-page.test.tsx`
Expected: PASS. If a test reads the preview by `getByText('/books/krew-elfow.md')` and fails because of the `Path:` prefix, query the `code` element instead (`screen.getByText('/books/krew-elfow.md', { selector: 'code' })`).

- [ ] **Step 6: Format and commit**

Run: `npm run format`
Run: `git add frontend/src/routes/_app/new.tsx frontend/src/components/Sidebar.tsx frontend/src/routeTree.gen.ts frontend/src/test/new-page.test.tsx`
Run: `git commit -m "feat: new page form for any page type [#111]"`

---

### Task 5: Final verification

- [ ] **Step 1: Frontend gates**

Run: `npm run typecheck`
Run: `npm run lint`
Run: `npm run format:check`
Run: `npm run test`
Run: `npm run build`
Run: `git diff --exit-code src/routeTree.gen.ts`
Expected: all green; baseline test count plus the new tests; no diff in `routeTree.gen.ts` after the build

- [ ] **Step 2: Whole gate**

Run (from the worktree root): `make verify ENV_FILE=../../../infra/.env`
Expected: ruff, backend tests, ESLint, Prettier check, typecheck, Vitest and build all green

- [ ] **Step 3: Manual smoke (Done when 2, 3, 4)**

Run: `make dev-up`, then `npm run dev`, open http://localhost:5173 and log in. Create the book "Krew elfów" (empty Szablon under `/books/krew-elfow`), a character with a book (frontmatter `book: /books/...`), and the same book again (backend error in the alert, nothing overwritten).
Expected: matches the mockup `docs/mockups/new-page-form.html`; the new Strony appear in the sidebar

- [ ] **Step 4: Commit formatting leftovers**

Run: `git status --short`
If anything is listed: `git add -A frontend/src` then `git commit -m "style: format [#111]"`
