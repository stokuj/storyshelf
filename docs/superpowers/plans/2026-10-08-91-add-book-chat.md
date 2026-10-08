# Add-book Chat and Empty Page Implementation Plan (#91)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The user adds a book by chatting with a fake Agent (Candidate cards), confirms one to get an empty template Page that appears in the sidebar, then runs Generate (loading state → filled content) — all on the fake store.

**Architecture:** `slugify` + `bookPath` in `src/wiki.ts` give one Path rule for store and UI. The fake store (`src/api/store.ts`) gets `searchCandidates` (word match + fallback), `createBook` and `generatePage`, both recording Versions through the existing `writePage`. `src/api/hooks.ts` wraps them in mutations with a fake Agent delay. New route `routes/add.tsx` holds the chat in component state; `routes/$.tsx` shows a Generate card on draft books; the sidebar links to `/add`.

**Tech Stack:** React 19, TanStack Router + Query v5, `yaml` (installed), Tailwind v4, Vitest + Testing Library (no jest-dom).

**Spec:** `docs/superpowers/specs/2026-10-08-91-add-book-chat.md`

## Global Constraints

- No new dependencies
- Book Path: `/books/${slugify(title)}.md`; slug is ASCII `[a-z0-9-]`, `ł→l`, no `-` at the ends
- Empty Page frontmatter: `type: book`, `title`, `author`, `year`, `status: draft`; body = `TEMPLATES.book` headings, no content; Version `created` / `human`
- After Generate: no `status`, `description` set, `generated: { by: agent:fake, at: <ISO now> }`; Version `generation` / `agent`
- Fake Agent delay: 1500 ms, 50 ms when `import.meta.env.MODE === 'test'`
- UI copy, verbatim: `Add book` (sidebar), `Add a book`, `Type a title, or just what you remember from the story.`, `Message to Agent`, `Send`, `Thinking…`, `Is it one of these?`, `I'm not sure. Maybe one of these?`, `Yes, add`, `Already in Wiki`, `None of these`, `Try a different title or author.`, `This page is empty`, `Generate with Agent`, `Generating…`
- Error messages, verbatim: `Page already exists: <path>`, `Only an empty book page can be generated`
- Store writes replace objects (new references), never mutate in place
- All commands run from `frontend/`; `make verify` from the worktree root before PR
- Commit titles ≤ 50 chars, conventional commits, no `Co-Authored-By`; one simple git command per call (worktree guard)

## Review Focus

1. Title with YAML-special characters (`Diuna: Mesjasz`) still yields valid frontmatter and a clean slug — test in Task 2
2. Prompt made only of short or unknown words (`Dodaj wiedźmina tom 1`) still shows cards (fallback), never an empty reply — tests in Tasks 2 and 3
3. Whitespace-only prompt cannot be sent — test in Task 3
4. Generate card never shows on a draft that is not a book (`/characters/snaut--solaris.md` is `draft`) — test in Task 4
5. A pending Generate on one Page does not leak its "Generating…" state into another Page (card keyed by path) — covered by `key={page.path}` in Task 4; reviewer checks it

---

### Task 0: Worktree setup

- [ ] **Step 1: Install dependencies**

Run: `npm ci`
Expected: completes without errors

- [ ] **Step 2: Baseline**

Run: `npm run test`
Expected: all existing tests PASS (58)

---

### Task 1: `slugify` and `bookPath` in `wiki.ts`

**Files:**
- Modify: `frontend/src/wiki.ts` (append after `pagePath`)
- Test: `frontend/src/wiki.test.ts`

**Interfaces:**
- Produces (from `@/wiki`):
  - `slugify(text: string): string`
  - `bookPath(title: string): string` — `/books/<slug>.md`

- [ ] **Step 1: Write the failing test**

In `frontend/src/wiki.test.ts` add `bookPath` and `slugify` to the `@/wiki` import (keep it alphabetical) and append:

```ts
test('slugify makes ASCII path slugs', () => {
  expect(slugify('Krew elfów')).toBe('krew-elfow')
  expect(slugify('Ostatnie życzenie')).toBe('ostatnie-zyczenie')
  expect(slugify('Łódź, Ślęża!')).toBe('lodz-sleza')
  expect(slugify('  Diuna: Mesjasz  ')).toBe('diuna-mesjasz')
})

test('bookPath matches every fixture book', () => {
  for (const p of listPages('book')) expect(bookPath(p.title)).toBe(p.path)
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run src/wiki.test.ts`
Expected: FAIL — `slugify` is not exported

- [ ] **Step 3: Implement**

In `frontend/src/wiki.ts`, right after the `pagePath` line:

```ts

// ASCII slug for Paths (spike #94: the app slugs names, not the model); 'Krew elfów' → 'krew-elfow'
export const slugify = (text: string) =>
  text
    .replace(/ł/g, 'l')
    .replace(/Ł/g, 'L')
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')

export const bookPath = (title: string) => `/books/${slugify(title)}.md`
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run src/wiki.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/wiki.ts src/wiki.test.ts
```
```bash
git commit -m "feat: slugify and bookPath helpers [#91]"
```

---

### Task 2: Store — Candidates, `createBook`, `generatePage`

**Files:**
- Modify: `frontend/src/api/fixtures/records.ts:85-89` (candidates)
- Modify: `frontend/src/api/store.ts` (imports, `searchCandidates`, two new exports)
- Modify: `frontend/src/api/hooks.ts` (adapt `useCandidates` call site temporarily — see Step 3)
- Test: `frontend/src/api/api.test.ts`

**Interfaces:**
- Consumes: `slugify`, `bookPath`, `TEMPLATES`, `parsePage` from `@/wiki`
- Produces (from `@/api/store`):
  - `searchCandidates(prompt: string): { matched: boolean; candidates: Candidate[] }`
  - `createBook(c: Candidate): Page` — throws `Page already exists: <path>`
  - `generatePage(path: string): Page` — throws `Only an empty book page can be generated`

- [ ] **Step 1: Write the failing tests**

In `frontend/src/api/api.test.ts`:
- change `import { parsePage } from '@/wiki'` to `import { parsePage, validateEdit } from '@/wiki'`
- add `createBook`, `generatePage`, `searchCandidates` to the `./store` import (alphabetical)
- append:

```ts
const titles = (prompt: string) => searchCandidates(prompt).candidates.map((c) => c.title)

test('searchCandidates matches title or author words, ignoring case and diacritics', () => {
  expect(titles('lalka')).toEqual(['Lalka'])
  expect(titles('Dodaj LEM').sort()).toEqual(['Niezwyciężony', 'Solaris'])
  expect(titles('krew elfow')).toEqual(['Krew elfów'])
  expect(searchCandidates('sapkowski').matched).toBe(true)
})

test('searchCandidates falls back to books not yet in the wiki', () => {
  const result = searchCandidates('Dodaj wiedźmina tom 1')
  expect(result.matched).toBe(false)
  expect(result.candidates.map((c) => c.title)).toEqual([
    'Miecz przeznaczenia',
    'Lalka',
    'Niezwyciężony',
  ])
})

const lalka = { title: 'Lalka', author: 'Bolesław Prus', year: 1890, cover_url: null }

test('createBook adds an empty template page with a created version', () => {
  const page = createBook({ ...lalka, title: 'Diuna: Mesjasz' })
  expect(page.path).toBe('/books/diuna-mesjasz.md')
  expect(page.title).toBe('Diuna: Mesjasz')
  expect(validateEdit(page.content, 'book')).toBeNull()
  expect(parsePage(page.content).frontmatter.status).toBe('draft')
  expect(parsePage(page.content).body).toBe(
    '## Streszczenie\n\n## Postacie\n\n## Miejsca\n\n## Wątki i motywy\n',
  )
  expect(listPages('book').map((p) => p.path)).toContain(page.path)
  expect(listVersions(page.path).map((v) => [v.kind, v.author])).toEqual([['created', 'human']])
})

test('createBook refuses a path that already exists', () => {
  expect(() => createBook({ ...lalka, title: 'Solaris' })).toThrow(
    'Page already exists: /books/solaris.md',
  )
})

test('generatePage fills a draft book exactly once', () => {
  const { path } = createBook(lalka)
  const page = generatePage(path)
  const fm = parsePage(page.content).frontmatter
  expect(fm.status).toBeUndefined()
  expect(fm.generated?.by).toBe('agent:fake')
  expect(fm.description).toBeTruthy()
  expect(validateEdit(page.content, 'book')).toBeNull()
  expect(page.content).toContain('(/characters/bohater--lalka.md)')
  expect(listVersions(path)[0]).toMatchObject({ kind: 'generation', author: 'agent' })
  expect(() => generatePage(path)).toThrow('Only an empty book page can be generated')
  expect(() => generatePage('/characters/snaut--solaris.md')).toThrow(
    'Only an empty book page can be generated',
  )
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npx vitest run src/api/api.test.ts`
Expected: FAIL — `createBook` is not exported

- [ ] **Step 3: Implement**

`frontend/src/api/fixtures/records.ts` — replace the `candidates` array:

```ts
// The first three already have Pages (duplicate case); the rest are new books
export const candidates: Candidate[] = [
  { title: 'Ostatnie życzenie', author: 'Andrzej Sapkowski', year: 1993, cover_url: null },
  { title: 'Krew elfów', author: 'Andrzej Sapkowski', year: 1994, cover_url: null },
  { title: 'Solaris', author: 'Stanisław Lem', year: 1961, cover_url: null },
  { title: 'Miecz przeznaczenia', author: 'Andrzej Sapkowski', year: 1992, cover_url: null },
  { title: 'Lalka', author: 'Bolesław Prus', year: 1890, cover_url: null },
  { title: 'Niezwyciężony', author: 'Stanisław Lem', year: 1964, cover_url: null },
]
```

`frontend/src/api/store.ts`:
- add `import { stringify } from 'yaml'` as the first import
- change the `@/wiki` import to `import { addVerified, bookPath, parsePage, slugify, TEMPLATES, validateEdit } from '@/wiki'` (let Prettier wrap it)
- replace `searchCandidates` and append the two new functions:

```ts
// Fake Agent: prompt words (≥3 letters) found in a title or author; none → books not yet in the Wiki
export function searchCandidates(prompt: string): { matched: boolean; candidates: Candidate[] } {
  const words = slugify(prompt)
    .split('-')
    .filter((w) => w.length >= 3)
  const found = candidates.filter((c) =>
    words.some((w) => slugify(`${c.title} ${c.author}`).includes(w)),
  )
  if (found.length) return { matched: true, candidates: found }
  const fresh = candidates.filter((c) => !pages.has(bookPath(c.title)))
  return { matched: false, candidates: fresh.slice(0, 3) }
}

// Kandydat confirmed → Page with an empty Szablon (ARCHITECTURE flow 1)
export function createBook(c: Candidate): Page {
  const path = bookPath(c.title)
  if (pages.has(path)) throw new Error(`Page already exists: ${path}`)
  const meta = { type: 'book', title: c.title, author: c.author, year: c.year, status: 'draft' }
  const body = TEMPLATES.book.map((h) => `## ${h}\n`).join('\n')
  const content = `---\n${stringify(meta)}---\n\n${body}`
  pages.set(path, toPage(path, content))
  return writePage(path, content, 'created', 'human')
}

// Generowanie (fake): fills an empty book once; the app, not the model, stamps `generated` (spike #94)
export function generatePage(path: string): Page {
  const page = getPage(path)
  const fm = parsePage(page.content).frontmatter
  if (page.type !== 'book' || fm.status !== 'draft') {
    throw new Error('Only an empty book page can be generated')
  }
  const slug = path.slice('/books/'.length, -'.md'.length)
  const meta = {
    ...fm,
    description: 'Strona wygenerowana przez fake Agenta.',
    generated: { by: 'agent:fake', at: new Date().toISOString() },
  }
  delete meta.status
  const body = [
    `## Streszczenie\n\n„${page.title}” (${fm.author}) — streszczenie wygenerowane przez Agenta (fake, M1).`,
    `## Postacie\n\n- [Bohater](/characters/bohater--${slug}.md) — główna postać`,
    `## Miejsca\n\n- [Miasto](/places/miasto--${slug}.md) — miejsce akcji`,
    '## Wątki i motywy\n\n- Motyw przewodni — do opisania',
  ].join('\n\n')
  return writePage(path, `---\n${stringify(meta)}---\n\n${body}\n`, 'generation', 'agent')
}
```

`frontend/src/api/hooks.ts` — `useCandidates` now breaks on the new return type and has no callers; delete the whole `useCandidates` export and drop `searchCandidates` from the `./store` import (Task 3 adds the mutation that replaces it).

- [ ] **Step 4: Run tests to verify they pass**

Run: `npx vitest run src/api/api.test.ts`
Expected: PASS

Run: `npm run typecheck`
Expected: no errors

- [ ] **Step 5: Commit**

```bash
git add src/api
```
```bash
git commit -m "feat: fake store creates and generates books [#91]"
```

---

### Task 3: `/add` chat route and sidebar link

**Files:**
- Create: `frontend/src/routes/add.tsx`
- Modify: `frontend/src/api/hooks.ts` (two mutations + delay)
- Modify: `frontend/src/components/Sidebar.tsx` (link after the `StoryShelf` link)
- Modify: `frontend/src/routeTree.gen.ts` (regenerated by the router plugin — never edit by hand)
- Test: `frontend/src/test/add-book.test.tsx`

**Interfaces:**
- Consumes: `searchCandidates`, `createBook` (Task 2); `bookPath`, `pageSplat` from `@/wiki`
- Produces (from `@/api/hooks`):
  - `agentDelay(): Promise<void>` (module-private)
  - `useSuggestCandidates()` — mutation `(prompt: string) => { matched; candidates }`
  - `useCreateBook()` — mutation `(c: Candidate) => Page`, invalidates `['pages']`

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/test/add-book.test.tsx`:

```tsx
import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { renderApp } from './renderApp'

async function ask(prompt: string) {
  const input = await screen.findByRole('textbox', { name: 'Message to Agent' })
  fireEvent.change(input, { target: { value: prompt } })
  fireEvent.click(screen.getByRole('button', { name: 'Send' }))
}

test('confirming a candidate opens a new empty page listed in the sidebar', async () => {
  const router = renderApp('/')
  fireEvent.click(await screen.findByRole('link', { name: 'Add book' }))
  await ask('Lalka')
  const card = await screen.findByRole('article', { name: 'Lalka' })
  within(card).getByText('Bolesław Prus · 1890')
  fireEvent.click(within(card).getByRole('button', { name: 'Yes, add' }))
  await waitFor(() => expect(router.state.location.pathname).toBe('/books/lalka'))
  const main = screen.getByRole('main')
  await within(main).findByRole('heading', { level: 1, name: 'Lalka' })
  within(main).getByRole('heading', { name: 'Wątki i motywy' })
  within(main).getByText('draft')
  const nav = screen.getByRole('navigation', { name: 'Wiki' })
  await within(nav).findByRole('link', { name: 'Lalka' })
})

test('a candidate already in the wiki links to its page', async () => {
  renderApp('/add')
  await ask('Solaris')
  const card = await screen.findByRole('article', { name: 'Solaris' })
  expect(within(card).queryByRole('button', { name: 'Yes, add' })).toBeNull()
  const link = within(card).getByRole('link', { name: 'Already in Wiki' })
  expect(link.getAttribute('href')).toBe('/books/solaris')
})

test('an unknown request falls back to books outside the wiki', async () => {
  renderApp('/add')
  await ask('Dodaj wiedźmina tom 1')
  await screen.findByText("I'm not sure. Maybe one of these?")
  expect(screen.getAllByRole('button', { name: 'Yes, add' })).toHaveLength(3)
})

test('None of these hides the cards', async () => {
  renderApp('/add')
  await ask('Lalka')
  await screen.findByText('Is it one of these?')
  fireEvent.click(screen.getByRole('button', { name: 'None of these' }))
  screen.getByText('Try a different title or author.')
  expect(screen.queryByRole('article')).toBeNull()
})

test('a blank message cannot be sent', async () => {
  renderApp('/add')
  const input = await screen.findByRole('textbox', { name: 'Message to Agent' })
  fireEvent.change(input, { target: { value: '   ' } })
  expect((screen.getByRole('button', { name: 'Send' }) as HTMLButtonElement).disabled).toBe(true)
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npx vitest run src/test/add-book.test.tsx`
Expected: FAIL — no `Add book` link / `/add` renders nothing

- [ ] **Step 3: Implement hooks**

`frontend/src/api/hooks.ts`:
- add `createBook` and `searchCandidates` to the `./store` import (alphabetical)
- change `import type { PageType } from './types'` to `import type { Candidate, PageType } from './types'`
- add after the `useProfile` line:

```ts
// Fake Agent latency (spike #94: real calls take 7–60 s); short in tests so pending states show
const FAKE_AGENT_MS = import.meta.env.MODE === 'test' ? 50 : 1500
const agentDelay = () => new Promise((resolve) => setTimeout(resolve, FAKE_AGENT_MS))

// One chat turn; the real Agent (M3) streams over SSE
export const useSuggestCandidates = () =>
  useMutation({
    mutationFn: async (prompt: string) => {
      await agentDelay()
      return searchCandidates(prompt)
    },
  })
```

- append after `useSavePage`:

```ts
export function useCreateBook() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (c: Candidate) => createBook(c),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['pages'] }),
  })
}
```

- [ ] **Step 4: Implement the route**

Create `frontend/src/routes/add.tsx`:

```tsx
// Add a book: chat with the Agent → Candidate cards → Page with an empty Szablon
import { Link, createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState } from 'react'
import { useCreateBook, usePages, useSuggestCandidates } from '@/api/hooks'
import type { Candidate } from '@/api/types'
import { bookPath, pageSplat } from '@/wiki'

export const Route = createFileRoute('/add')({
  component: AddBookPage,
})

// One exchange; the chat lives in component state until the real Agent (M3)
interface Turn {
  prompt: string
  matched: boolean
  candidates: Candidate[]
  dismissed: boolean
}

const button = 'rounded-md px-4 py-1.5 text-sm font-semibold disabled:opacity-50'
const bubble = 'ml-auto w-fit rounded-md bg-muted px-3 py-2'

function AddBookPage() {
  const [turns, setTurns] = useState<Turn[]>([])
  const [draft, setDraft] = useState('')
  const suggest = useSuggestCandidates()
  const dismiss = (i: number) =>
    setTurns((ts) => ts.map((t, j) => (j === i ? { ...t, dismissed: true } : t)))

  return (
    <section className="max-w-2xl">
      <h1 className="font-heading text-3xl">Add a book</h1>
      <p className="mt-1 text-muted-foreground">
        Type a title, or just what you remember from the story.
      </p>

      <ol aria-label="Chat" className="mt-6 space-y-6">
        {turns.map((t, i) => (
          <li key={i} className="space-y-3">
            <p className={bubble}>{t.prompt}</p>
            <p>{t.matched ? 'Is it one of these?' : "I'm not sure. Maybe one of these?"}</p>
            {t.dismissed ? (
              <p>Try a different title or author.</p>
            ) : (
              <>
                {t.candidates.map((c) => (
                  <CandidateCard key={c.title} candidate={c} />
                ))}
                <button type="button" onClick={() => dismiss(i)} className={`${button} border`}>
                  None of these
                </button>
              </>
            )}
          </li>
        ))}
        {suggest.isPending && (
          <li className="space-y-3">
            <p className={bubble}>{suggest.variables}</p>
            <p className="text-muted-foreground">Thinking…</p>
          </li>
        )}
      </ol>

      <form
        className="mt-6 flex gap-2"
        onSubmit={(e) => {
          e.preventDefault()
          const prompt = draft.trim()
          suggest.mutate(prompt, {
            onSuccess: (r) => setTurns((ts) => [...ts, { prompt, ...r, dismissed: false }]),
          })
          setDraft('')
        }}
      >
        <input
          aria-label="Message to Agent"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          className="flex-1 rounded-md border bg-background px-3 py-1.5"
        />
        <button
          type="submit"
          disabled={!draft.trim() || suggest.isPending}
          className={`${button} bg-primary text-primary-foreground`}
        >
          Send
        </button>
      </form>
    </section>
  )
}

function CandidateCard({ candidate: c }: { candidate: Candidate }) {
  const { data: pages = [] } = usePages()
  const create = useCreateBook()
  const navigate = useNavigate()
  const path = bookPath(c.title)
  const exists = pages.some((p) => p.path === path)

  return (
    <article aria-label={c.title} className="flex items-center gap-4 rounded-md border p-3">
      <span aria-hidden className="h-16 w-11 shrink-0 rounded-sm bg-muted" />
      <div className="flex-1">
        <h2 className="font-heading text-lg">{c.title}</h2>
        <p className="text-sm text-muted-foreground">{`${c.author} · ${c.year}`}</p>
        {create.error && (
          <p role="alert" className="mt-1 text-sm text-destructive">
            {create.error.message}
          </p>
        )}
      </div>
      {exists ? (
        <Link
          to="/$"
          params={{ _splat: pageSplat(path) }}
          className="text-sm font-semibold text-primary"
        >
          Already in Wiki
        </Link>
      ) : (
        <button
          type="button"
          disabled={create.isPending}
          onClick={() =>
            create.mutate(c, {
              onSuccess: (page) =>
                navigate({ to: '/$', params: { _splat: pageSplat(page.path) } }),
            })
          }
          className={`${button} bg-primary text-primary-foreground`}
        >
          Yes, add
        </button>
      )}
    </article>
  )
}
```

- [ ] **Step 5: Sidebar link**

`frontend/src/components/Sidebar.tsx` — insert right after the closing `</Link>` of the `StoryShelf` link:

```tsx
      <Link
        to="/add"
        className="rounded-md border px-2 py-1 text-center text-sm font-semibold hover:bg-background"
        activeProps={{ className: 'bg-background text-primary' }}
      >
        Add book
      </Link>
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `npx vitest run src/test/add-book.test.tsx`
Expected: PASS (5 tests). The router plugin regenerates `src/routeTree.gen.ts` with `/add`.

Run: `npm run test && npm run typecheck && npm run lint`
Expected: all PASS — sidebar section counts in `app.test.tsx` are unchanged (the new link sits outside the type sections)

- [ ] **Step 7: Commit**

```bash
git add src/routes/add.tsx src/routeTree.gen.ts src/api/hooks.ts src/components/Sidebar.tsx src/test/add-book.test.tsx
```
```bash
git commit -m "feat: add-book chat with candidate cards [#91]"
```

---

### Task 4: Generate card on an empty book Page

**Files:**
- Modify: `frontend/src/api/hooks.ts` (one mutation)
- Modify: `frontend/src/routes/$.tsx` (imports, render the card, new component)
- Test: `frontend/src/test/add-book.test.tsx`

**Interfaces:**
- Consumes: `generatePage` (Task 2), `agentDelay` (Task 3), `parsePage` from `@/wiki`
- Produces: `useGeneratePage(path: string)` — mutation `() => Page`, refreshes the Page and the sidebar

- [ ] **Step 1: Write the failing tests**

Append to `frontend/src/test/add-book.test.tsx`:

```tsx
test('Generate fills an empty book page', async () => {
  renderApp('/add')
  await ask('Lalka')
  const card = await screen.findByRole('article', { name: 'Lalka' })
  fireEvent.click(within(card).getByRole('button', { name: 'Yes, add' }))
  fireEvent.click(await screen.findByRole('button', { name: 'Generate with Agent' }))
  await screen.findByRole('button', { name: 'Generating…' })
  await screen.findByText(/streszczenie wygenerowane przez Agenta/)
  const main = screen.getByRole('main')
  expect(within(main).queryByRole('heading', { name: 'This page is empty' })).toBeNull()
  expect(within(main).queryByText('draft')).toBeNull()
})

test('a draft that is not a book has no Generate button', async () => {
  renderApp('/characters/snaut--solaris')
  await screen.findByRole('heading', { level: 1, name: 'Snaut' })
  expect(screen.queryByRole('button', { name: 'Generate with Agent' })).toBeNull()
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npx vitest run src/test/add-book.test.tsx`
Expected: FAIL — `Generate with Agent` button not found (the Snaut test may already pass; that is fine)

- [ ] **Step 3: Implement the hook**

`frontend/src/api/hooks.ts` — add `generatePage` to the `./store` import and append after `useCreateBook`:

```ts
export function useGeneratePage(path: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      await agentDelay()
      return generatePage(path)
    },
    onSuccess: () => refreshPage(qc, path),
  })
}
```

- [ ] **Step 4: Implement the card**

`frontend/src/routes/$.tsx`:
- change the hooks import to `import { useGeneratePage, usePage, usePages, useProposals } from '@/api/hooks'`
- change the wiki import to `import { pagePath, pageSplat, parsePage, universeMembers } from '@/wiki'`
- in `PageRoute`, between `<PageActions page={page} />` and `<OpenProposals page={page} />` add:

```tsx
      <GenerateCard key={page.path} page={page} />
```

- add after the `PageActions` function:

```tsx
// Generowanie: the Agent fills an empty (draft) book once; later changes come as Proposals
function GenerateCard({ page }: { page: Page }) {
  const generate = useGeneratePage(page.path)
  if (page.type !== 'book' || parsePage(page.content).frontmatter.status !== 'draft') return null
  return (
    <section className="mb-6 rounded-md border bg-muted p-4">
      <h2 className="font-heading text-xl">This page is empty</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        The Agent writes the summary, characters and places. The first generation is saved
        directly; later changes come as proposals.
      </p>
      <button
        type="button"
        disabled={generate.isPending}
        onClick={() => generate.mutate()}
        className="mt-3 rounded-md bg-primary px-4 py-1.5 text-sm font-semibold text-primary-foreground disabled:opacity-50"
      >
        {generate.isPending ? 'Generating…' : 'Generate with Agent'}
      </button>
      {generate.error && (
        <p role="alert" className="mt-2 text-sm text-destructive">
          {generate.error.message}
        </p>
      )}
    </section>
  )
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `npx vitest run src/test/add-book.test.tsx`
Expected: PASS (7 tests)

- [ ] **Step 6: Commit**

```bash
git add src/api/hooks.ts 'src/routes/$.tsx' src/test/add-book.test.tsx
```
```bash
git commit -m "feat: generate an empty book page [#91]"
```

---

### Task 5: Full verification

- [ ] **Step 1: Frontend gates**

Run: `npm run format && npm run typecheck && npm run lint && npm run test && npm run build`
Expected: all PASS; `git status` shows no change to `src/routeTree.gen.ts` after the build

- [ ] **Step 2: Commit formatting, if any**

Run: `git status --short`
If Prettier changed files: `git add -u` then `git commit -m "style: format [#91]"`

- [ ] **Step 3: CI equivalent**

From the worktree root: `make verify` (if it needs `infra/.env`, pass `ENV_FILE=/home/dv6/GitHub/storyshelf/infra/.env` as in #90)
Expected: backend tests, ruff, frontend gates all green
