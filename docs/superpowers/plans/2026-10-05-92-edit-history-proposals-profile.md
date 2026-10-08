# Edit, History, Proposals and Profile Implementation Plan (#92)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The user can edit a Page as raw `.md` (validated against its Template), browse its Version history and view old Versions read-only, review Agent Proposals as a line diff and accept or reject them (stale ones blocked), and see their Profile with favourite cards — all on the fake store.

**Architecture:** Pure helpers in `src/wiki.ts` (`parsePage` hardened, `TEMPLATES`, `validateEdit`, `addVerified`). The fake store in `src/api/store.ts` gets writes (`savePage`, `acceptProposal`, `rejectProposal`, `setProfilePublic`) that validate like a future API and replace objects immutably; `resetStore` reseeds it after every test. `src/api/hooks.ts` wraps writes in `useMutation` + invalidation. The splat route `routes/$.tsx` switches views by search params (`?view=edit|history|proposal`, `v`, `p`); new components `PageEditor`, `PageHistory`, `ProposalView`; new route `routes/profile.tsx`.

**Tech Stack:** React 19, TanStack Router + Query v5, `yaml` (already installed), `diff` (jsdiff, new), Tailwind v4, Vitest + Testing Library (no jest-dom).

**Spec:** `docs/superpowers/specs/2026-10-05-92-edit-history-proposals-profile.md`

## Global Constraints

- Only new dependency: `diff`. No jest-dom, no shadcn components
- Required headings, verbatim: book `Streszczenie, Postacie, Miejsca, Wątki i motywy`; character `Opis, Rola w książce, Powiązania`; place `Opis, Rola w książce`; universe `Opis`
- Error messages, verbatim: `Invalid frontmatter: <message>`, `Invalid frontmatter: not a mapping`, `Page type can't change`, `Missing template headings: <A, B>`, `Proposal is <status>`
- Verification event author: `human:${profile.handle}` (→ `human:stokuj`)
- Search params on `/$`: `view?: 'edit' | 'history' | 'proposal'`, `v?: number` (Version id), `p?: number` (Proposal id)
- Version label `vN` by position, oldest = v1
- Store writes replace objects (new references), never mutate in place
- UI labels in English (like the mockups)
- All commands run from `frontend/`; `make verify` from the worktree root before PR
- Commit titles ≤ 50 chars, conventional commits, no `Co-Authored-By`

## Review Focus

1. Failed save keeps the user's text in the textarea (no reset to the stored content) — test in Task 3
2. Cancel discards unsaved text and leaves History unchanged — test in Task 3
3. Unknown `?view=` value renders the normal page; unknown `v` shows "Version not found." — tests in Task 4
4. Two writes within the same millisecond still list newest first (tie-break on id) — test in Task 2
5. CRLF content (pasted from Windows) passes validation and saves — test in Task 1

---

### Task 0: Worktree setup

- [ ] **Step 1: Install dependencies** (skip if `node_modules` exists)

Run: `npm ci`
Expected: completes without errors

- [ ] **Step 2: Baseline**

Run: `npm run test`
Expected: all existing tests PASS

---

### Task 1: `wiki.ts` — hardened `parsePage`, `TEMPLATES`, `validateEdit`, `addVerified`

**Files:**
- Modify: `frontend/src/wiki.ts` (import line, `parsePage`, append new exports)
- Test: `frontend/src/wiki.test.ts`

**Interfaces:**
- Produces (from `@/wiki`):
  - `TEMPLATES: Record<PageType, string[]>`
  - `parsePage(content: string): { frontmatter: Frontmatter; body: string }` — accepts CRLF; empty block → `{}`
  - `validateEdit(content: string, type: PageType): string | null`
  - `addVerified(content: string, by: string, at: string): string`

- [ ] **Step 1: Write the failing tests** (extend the import, append tests to `src/wiki.test.ts`)

```ts
import { getPage, listPages } from '@/api/store'
import {
  addVerified,
  groupByType,
  pagePath,
  pageSplat,
  parsePage,
  universeMembers,
  validateEdit,
} from '@/wiki'
```

```ts
const OZ = getPage('/books/ostatnie-zyczenie.md').content

test('parsePage accepts CRLF line endings', () => {
  const crlf = parsePage(OZ.replaceAll('\n', '\r\n'))
  expect(crlf.frontmatter).toEqual(parsePage(OZ).frontmatter)
  expect(crlf.body.startsWith('## Streszczenie')).toBe(true)
})

test('parsePage treats an empty frontmatter block as {}', () => {
  expect(parsePage('---\n---\n## Opis\n')).toEqual({ frontmatter: {}, body: '## Opis\n' })
})

test('every fixture page passes validateEdit', () => {
  for (const p of pages) expect(validateEdit(p.content, p.type), p.path).toBeNull()
})

test('validateEdit accepts CRLF content', () => {
  expect(validateEdit(OZ.replaceAll('\n', '\r\n'), 'book')).toBeNull()
})

test('validateEdit rejects broken YAML', () => {
  expect(validateEdit(OZ.replace('type: book', 'type: [book'), 'book')).toMatch(
    /^Invalid frontmatter: /,
  )
})

test('validateEdit rejects a frontmatter that is not a mapping', () => {
  expect(validateEdit('---\njust text\n---\n## Opis\n', 'universe')).toBe(
    'Invalid frontmatter: not a mapping',
  )
})

test('validateEdit rejects a type change', () => {
  expect(validateEdit(OZ.replace('type: book', 'type: universe'), 'book')).toBe(
    "Page type can't change",
  )
})

test('validateEdit lists missing template headings', () => {
  const content = OZ.replace('## Postacie\n', '').replace('## Miejsca\n', '')
  expect(validateEdit(content, 'book')).toBe('Missing template headings: Postacie, Miejsca')
})

test('addVerified appends to an existing verified list and keeps the body', () => {
  const out = addVerified(OZ, 'human:stokuj', '2026-10-05T10:00:00.000Z')
  expect(parsePage(out).frontmatter.verified).toEqual([
    { by: 'human:stokuj', at: '2026-10-02T08:30:00Z' },
    { by: 'human:stokuj', at: '2026-10-05T10:00:00.000Z' },
  ])
  expect(parsePage(out).body).toBe(parsePage(OZ).body)
})

test('addVerified creates the verified list when missing', () => {
  const out = addVerified('---\ntype: universe\n---\n## Opis\n', 'human:x', 't')
  expect(parsePage(out)).toEqual({
    frontmatter: { type: 'universe', verified: [{ by: 'human:x', at: 't' }] },
    body: '## Opis\n',
  })
})
```

- [ ] **Step 2: Run to verify they fail**

Run: `npx vitest run src/wiki.test.ts`
Expected: FAIL — `validateEdit` / `addVerified` are not exported; CRLF and empty-frontmatter tests throw `Missing frontmatter`

- [ ] **Step 3: Implement** in `src/wiki.ts`

Replace the `yaml` import:

```ts
import { isSeq, parse, parseDocument } from 'yaml'
```

Replace the whole `parsePage` function with:

```ts
// Opening `---`, optional YAML block, closing `---`; LF or CRLF
const FRONTMATTER = /^---\r?\n(?:([\s\S]*?)\r?\n)?---(?:\r?\n|$)/

export function parsePage(content: string): { frontmatter: Frontmatter; body: string } {
  const match = FRONTMATTER.exec(content)
  if (!match) throw new Error('Missing frontmatter')
  return {
    frontmatter: (parse(match[1] ?? '') ?? {}) as Frontmatter,
    body: content.slice(match[0].length).trimStart(),
  }
}

// Szablon: `##` headings every Page of a type must keep
export const TEMPLATES: Record<PageType, string[]> = {
  book: ['Streszczenie', 'Postacie', 'Miejsca', 'Wątki i motywy'],
  character: ['Opis', 'Rola w książce', 'Powiązania'],
  place: ['Opis', 'Rola w książce'],
  universe: ['Opis'],
}

// First problem that blocks saving an Edycja, or null
export function validateEdit(content: string, type: PageType): string | null {
  let parsed
  try {
    parsed = parsePage(content)
  } catch (e) {
    return `Invalid frontmatter: ${(e as Error).message}`
  }
  const fm: unknown = parsed.frontmatter
  if (typeof fm !== 'object' || fm === null || Array.isArray(fm)) {
    return 'Invalid frontmatter: not a mapping'
  }
  // type picks the Path directory, so changing it would break the Page identity
  if (parsed.frontmatter.type !== type) return "Page type can't change"
  const lines = new Set(parsed.body.split('\n').map((l) => l.trim()))
  const missing = TEMPLATES[type].filter((h) => !lines.has(`## ${h}`))
  return missing.length ? `Missing template headings: ${missing.join(', ')}` : null
}

// Appends a Weryfikacja event (OKF v0.2 §5.2) without reformatting the rest of the frontmatter
export function addVerified(content: string, by: string, at: string): string {
  const match = FRONTMATTER.exec(content)
  if (!match) throw new Error('Missing frontmatter')
  const doc = parseDocument(match[1] ?? '')
  const event = { by, at }
  const list = doc.get('verified')
  if (isSeq(list)) list.add(doc.createNode(event))
  else doc.set('verified', doc.createNode([event]))
  return `---\n${String(doc)}---\n${content.slice(match[0].length)}`
}
```

- [ ] **Step 4: Run tests**

Run: `npx vitest run src/wiki.test.ts`
Expected: PASS (old and new)

- [ ] **Step 5: Commit**

```bash
git add src/wiki.ts src/wiki.test.ts
git commit -m "feat: template check and verified event [#92]"
```

---

### Task 2: Store writes, reset between tests, mutation hooks

**Files:**
- Modify: `frontend/src/api/store.ts` (whole file below)
- Modify: `frontend/src/api/hooks.ts` (imports + new hooks)
- Create: `frontend/src/test/setup.ts`
- Modify: `frontend/vite.config.ts` (`test.setupFiles`)
- Test: `frontend/src/api/api.test.ts`

**Interfaces:**
- Consumes: `parsePage`, `validateEdit`, `addVerified` from `@/wiki` (Task 1)
- Produces (from `@/api/store`): `resetStore(): void`, `savePage(path: string, content: string): Page`, `getProposal(id: number): Proposal`, `acceptProposal(id: number): Page`, `rejectProposal(id: number): void`, `setProfilePublic(value: boolean): Profile`; `listProposals` now returns `status: 'stale'` for outdated open proposals
- Produces (from `@/api/hooks`): `useSavePage(path)` → mutate(`content: string`), `useAcceptProposal(path)` / `useRejectProposal(path)` → mutate(`id: number`), `useSetProfilePublic()` → mutate(`value: boolean`)

- [ ] **Step 1: Write the failing tests** (append to `src/api/api.test.ts`; replace its store import)

```ts
import { parsePage } from '@/wiki'
import {
  acceptProposal,
  getPage,
  getProfile,
  listPages,
  listProposals,
  listVersions,
  rejectProposal,
  resetStore,
  savePage,
  setProfilePublic,
} from './store'
```

```ts
const OZ = '/books/ostatnie-zyczenie.md'
const KE = '/books/krew-elfow.md'
const retitle = (title: string) =>
  getPage(KE).content.replace('title: Krew elfów', `title: ${title}`)

test('savePage stores the content and adds an edit version on top', () => {
  const content = retitle('Krew elfów (wyd. 2)')
  expect(savePage(KE, content).title).toBe('Krew elfów (wyd. 2)')
  expect(getPage(KE).content).toBe(content)
  expect(listVersions(KE)[0]).toMatchObject({ kind: 'edit', author: 'human', content })
  expect(listPages('book').map((p) => p.title)).toContain('Krew elfów (wyd. 2)')
})

test('savePage rejects an invalid edit and keeps the page', () => {
  const before = getPage(KE)
  expect(() => savePage(KE, before.content.replace('## Postacie\n', ''))).toThrow(
    'Missing template headings: Postacie',
  )
  expect(getPage(KE)).toBe(before)
  expect(listVersions(KE)).toHaveLength(1)
})

test('two edits in the same millisecond list newest first', () => {
  vi.useFakeTimers({ now: new Date('2026-10-05T10:00:00Z') })
  savePage(KE, retitle('A'))
  savePage(KE, retitle('B'))
  vi.useRealTimers()
  expect(parsePage(listVersions(KE)[0].content).frontmatter.title).toBe('B')
})

test('resetStore restores the fixtures', () => {
  savePage(KE, retitle('Zmieniony'))
  resetStore()
  expect(getPage(KE).title).toBe('Krew elfów')
  expect(listVersions(KE)).toHaveLength(1)
})

test('accepting an open proposal adds a proposal version and a verified event', () => {
  expect(listProposals(OZ)[0].status).toBe('open')
  const page = acceptProposal(1)
  expect(page.content).toContain('[Nivellen]')
  expect(parsePage(page.content).frontmatter.verified).toHaveLength(2)
  expect(listVersions(OZ)[0]).toMatchObject({ kind: 'proposal', author: 'agent' })
  expect(listProposals(OZ)[0].status).toBe('accepted')
})

test('rejecting a proposal changes neither the page nor history', () => {
  const before = getPage(OZ)
  rejectProposal(1)
  expect(getPage(OZ)).toBe(before)
  expect(listVersions(OZ)).toHaveLength(3)
  expect(listProposals(OZ)[0].status).toBe('rejected')
  expect(() => acceptProposal(1)).toThrow('Proposal is rejected')
})

test('an edit makes an open proposal stale and blocks accept', () => {
  savePage(OZ, getPage(OZ).content + '\nDopisek.\n')
  expect(listProposals(OZ)[0].status).toBe('stale')
  expect(() => acceptProposal(1)).toThrow('Proposal is stale')
})

test('setProfilePublic replaces the profile object', () => {
  const before = getProfile()
  expect(setProfilePublic(false).is_public).toBe(false)
  expect(getProfile()).not.toBe(before)
})
```

- [ ] **Step 2: Run to verify they fail**

Run: `npx vitest run src/api/api.test.ts`
Expected: FAIL — `savePage`, `resetStore`, … are not exported

- [ ] **Step 3: Replace `src/api/store.ts`** with:

```ts
// In-memory fake of the wiki API, seeded from OKF fixtures. M2 replaces it with fetch('/api/...').
// Writes replace objects instead of mutating them, so React Query sees new data.
import {
  candidates,
  profile as seedProfile,
  proposals as seedProposals,
  versions as recordedVersions,
} from './fixtures/records'
import { addVerified, parsePage, validateEdit } from '@/wiki'
import type {
  Candidate,
  Page,
  PageType,
  PageVersion,
  Profile,
  Proposal,
  VersionKind,
} from './types'

const files = import.meta.glob<string>('./fixtures/**/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
})

let pages: Map<string, Page>
let versions: PageVersion[]
let proposals: Proposal[]
let profile: Profile

function toPage(path: string, content: string): Page {
  const fm = parsePage(content).frontmatter
  return {
    path,
    type: fm.type,
    title: fm.title ?? path,
    book: fm.book ?? null,
    universe: fm.universe ?? null,
    content,
  }
}

// Seeds every record from the fixtures; tests reseed after each case (src/test/setup.ts)
export function resetStore() {
  pages = new Map()
  versions = []
  proposals = structuredClone(seedProposals)
  profile = structuredClone(seedProfile)

  for (const [file, content] of Object.entries(files)) {
    const path = file.replace('./fixtures', '') // OKF: file path = concept identity
    pages.set(path, toPage(path, content))

    const recorded = recordedVersions.filter((v) => v.page === path)
    if (recorded.length === 0) {
      const draft = parsePage(content).frontmatter.status === 'draft'
      versions.push({
        id: versions.length + 1000,
        page: path,
        kind: draft ? 'created' : 'generation',
        author: draft ? 'human' : 'agent',
        content,
        created_at: '2026-10-01T12:00:00Z',
      })
    } else {
      // The newest recorded version always holds the current page content
      const latest = recorded.length - 1
      recorded.forEach((v, i) =>
        versions.push({ ...v, content: i === latest ? content : v.content! }),
      )
    }
  }
}
resetStore()

// Same timestamp (two writes in one millisecond) → higher id is newer
const byNewest = <T extends { id: number; created_at: string }>(a: T, b: T) =>
  b.created_at.localeCompare(a.created_at) || b.id - a.id

export function listPages(type?: PageType): Page[] {
  return [...pages.values()]
    .filter((p) => !type || p.type === type)
    .sort((a, b) => a.title.localeCompare(b.title))
}

export function getPage(path: string): Page {
  const page = pages.get(path)
  if (!page) throw new Error(`Page not found: ${path}`)
  return page
}

export function listVersions(path: string): PageVersion[] {
  return versions.filter((v) => v.page === path).sort(byNewest)
}

// Stale = still open, but the Page got a newer Version than the one the Agent worked on
function withStatus(p: Proposal): Proposal {
  return p.status === 'open' && p.base_version !== listVersions(p.page)[0].id
    ? { ...p, status: 'stale' }
    : p
}

export function listProposals(path: string): Proposal[] {
  return proposals
    .filter((p) => p.page === path)
    .map(withStatus)
    .sort(byNewest)
}

export function getProposal(id: number): Proposal {
  const proposal = proposals.find((p) => p.id === id)
  if (!proposal) throw new Error(`Proposal not found: ${id}`)
  return withStatus(proposal)
}

// Validates like the future API (400) and records a Version
function writePage(
  path: string,
  content: string,
  kind: VersionKind,
  author: PageVersion['author'],
): Page {
  const error = validateEdit(content, getPage(path).type)
  if (error) throw new Error(error)
  const page = toPage(path, content)
  pages.set(path, page)
  versions.push({
    id: Math.max(...versions.map((v) => v.id)) + 1,
    page: path,
    kind,
    author,
    content,
    created_at: new Date().toISOString(),
  })
  return page
}

export function savePage(path: string, content: string): Page {
  return writePage(path, content, 'edit', 'human')
}

function openProposal(id: number): Proposal {
  const proposal = getProposal(id)
  if (proposal.status !== 'open') throw new Error(`Proposal is ${proposal.status}`)
  return proposal
}

function setStatus(id: number, status: Proposal['status']) {
  proposals = proposals.map((p) => (p.id === id ? { ...p, status } : p))
}

export function acceptProposal(id: number): Page {
  const proposal = openProposal(id)
  const content = addVerified(
    proposal.content,
    `human:${profile.handle}`,
    new Date().toISOString(),
  )
  const page = writePage(proposal.page, content, 'proposal', 'agent')
  setStatus(id, 'accepted')
  return page
}

export function rejectProposal(id: number): void {
  openProposal(id)
  setStatus(id, 'rejected')
}

export function getProfile(): Profile {
  return profile
}

export function setProfilePublic(value: boolean): Profile {
  profile = { ...profile, is_public: value }
  return profile
}

export function searchCandidates(query: string): Candidate[] {
  const q = query.toLowerCase()
  return candidates.filter((c) => c.title.toLowerCase().includes(q))
}
```

- [ ] **Step 4: Create `src/test/setup.ts`**

```ts
import { resetStore } from '@/api/store'

// The fake store is module state: every test starts from the fixtures
afterEach(resetStore)
```

- [ ] **Step 5: Register it in `vite.config.ts`** (inside `test`)

```ts
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
  },
```

- [ ] **Step 6: Add mutation hooks to `src/api/hooks.ts`**

Replace the two import blocks at the top with:

```ts
// Read hooks + writes; queryFn/mutationFn swap to the real /api/wiki/... endpoints in M2
import { type QueryClient, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  acceptProposal,
  getPage,
  getProfile,
  listPages,
  listProposals,
  listVersions,
  rejectProposal,
  savePage,
  searchCandidates,
  setProfilePublic,
} from './store'
```

(Delete the old `// Read hooks; …` comment line.) Append:

```ts
// A Page write touches the sidebar list and everything under ['page', path]
const refreshPage = (qc: QueryClient, path: string) =>
  Promise.all([
    qc.invalidateQueries({ queryKey: ['pages'] }),
    qc.invalidateQueries({ queryKey: ['page', path] }),
  ])

export function useSavePage(path: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (content: string) => savePage(path, content),
    onSuccess: () => refreshPage(qc, path),
  })
}

export function useAcceptProposal(path: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => acceptProposal(id),
    onSuccess: () => refreshPage(qc, path),
  })
}

export function useRejectProposal(path: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => rejectProposal(id),
    onSuccess: () => refreshPage(qc, path),
  })
}

export function useSetProfilePublic() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (value: boolean) => setProfilePublic(value),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['profile'] }),
  })
}
```

- [ ] **Step 7: Run all tests + typecheck**

Run: `npm run test && npm run typecheck`
Expected: PASS, no type errors

- [ ] **Step 8: Commit**

```bash
git add src/api/store.ts src/api/hooks.ts src/api/api.test.ts src/test/setup.ts vite.config.ts
git commit -m "feat: fake store writes and proposals [#92]"
```

---

### Task 3: Page actions and the editor (`?view=edit`)

**Files:**
- Modify: `frontend/src/routes/$.tsx` (`validateSearch`, view switch, `PageActions`)
- Create: `frontend/src/components/PageEditor.tsx`
- Test: `frontend/src/test/edit.test.tsx`

**Interfaces:**
- Consumes: `useSavePage(path)` (Task 2)
- Produces: route search `{ view?: 'edit' | 'history' | 'proposal'; v?: number; p?: number }` read via `Route.useSearch()`; `PageEditor({ page }: { page: Page })`; links named `Edit` and `History` above the page

- [ ] **Step 1: Write the failing tests** — create `src/test/edit.test.tsx`

```tsx
import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { renderApp } from './renderApp'

const source = async () =>
  (await screen.findByRole('textbox', { name: 'Page source' })) as HTMLTextAreaElement

function edit(textarea: HTMLTextAreaElement, change: (value: string) => string) {
  fireEvent.change(textarea, { target: { value: change(textarea.value) } })
}

test('Edit opens the editor with the raw page source', async () => {
  renderApp('/books/krew-elfow')
  fireEvent.click(await screen.findByRole('link', { name: 'Edit' }))
  expect((await source()).value.startsWith('---\ntype: book\n')).toBe(true)
})

test('saving an edit shows the new content', async () => {
  renderApp('/books/krew-elfow?view=edit')
  edit(await source(), (v) => v.replace('## Wątki i motywy', '## Wątki i motywy\n\nDopisek z edycji.'))
  fireEvent.click(screen.getByRole('button', { name: 'Save' }))
  await screen.findByText('Dopisek z edycji.')
  expect(screen.queryByRole('textbox', { name: 'Page source' })).toBeNull()
})

test('removing a template heading blocks save and keeps the text', async () => {
  renderApp('/books/solaris?view=edit')
  const textarea = await source()
  edit(textarea, (v) => v.replace('## Postacie\n', ''))
  const typed = textarea.value
  fireEvent.click(screen.getByRole('button', { name: 'Save' }))
  expect((await screen.findByRole('alert')).textContent).toBe(
    'Missing template headings: Postacie',
  )
  expect(textarea.value).toBe(typed)
})

test('cancel discards unsaved text', async () => {
  renderApp('/books/krew-elfow?view=edit')
  edit(await source(), (v) => v + '\nNiezapisane.\n')
  fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
  await waitFor(() => expect(screen.queryByRole('textbox', { name: 'Page source' })).toBeNull())
  expect(screen.queryByText('Niezapisane.')).toBeNull()
  within(screen.getByRole('main')).getByRole('heading', { level: 1, name: 'Krew elfów' })
})
```

- [ ] **Step 2: Run to verify they fail**

Run: `npx vitest run src/test/edit.test.tsx`
Expected: FAIL — no `Edit` link, no `Page source` textbox

- [ ] **Step 3: Create `src/components/PageEditor.tsx`**

```tsx
// Edycja: the raw .md in a textarea; the store validates it and records a Version
import { Link, useNavigate } from '@tanstack/react-router'
import { useState } from 'react'
import { useSavePage } from '@/api/hooks'
import type { Page } from '@/api/types'
import { pageSplat } from '@/wiki'

export function PageEditor({ page }: { page: Page }) {
  const [content, setContent] = useState(page.content)
  const save = useSavePage(page.path)
  const navigate = useNavigate()
  const params = { _splat: pageSplat(page.path) }
  const back = () => navigate({ to: '/$', params, search: {} })

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        save.mutate(content, { onSuccess: back })
      }}
    >
      <Link
        to="/$"
        params={params}
        search={{}}
        className="text-sm text-muted-foreground hover:text-primary"
      >
        ← {page.title}
      </Link>
      <h1 className="mt-2 font-heading text-3xl">Edit</h1>
      <textarea
        aria-label="Page source"
        value={content}
        onChange={(e) => setContent(e.target.value)}
        rows={30}
        spellCheck={false}
        className="mt-4 w-full rounded-md border bg-background p-3 font-mono text-sm"
      />
      {save.error && (
        <p role="alert" className="mt-2 text-sm text-destructive">
          {save.error.message}
        </p>
      )}
      <div className="mt-4 flex gap-2">
        <button
          type="submit"
          disabled={save.isPending}
          className="rounded-md bg-primary px-4 py-1.5 text-sm font-semibold text-primary-foreground"
        >
          Save
        </button>
        <button type="button" onClick={back} className="rounded-md border px-4 py-1.5 text-sm">
          Cancel
        </button>
      </div>
    </form>
  )
}
```

- [ ] **Step 4: Wire the route** in `src/routes/$.tsx`

Add the import:

```tsx
import { PageEditor } from '@/components/PageEditor'
```

Replace the `Route` definition with:

```tsx
const VIEWS = ['edit', 'history', 'proposal'] as const
type PageSearch = { view?: (typeof VIEWS)[number]; v?: number; p?: number }

export const Route = createFileRoute('/$')({
  // Unknown values are dropped, so a bad ?view= falls back to the page itself
  validateSearch: (s: Record<string, unknown>): PageSearch => ({
    view: VIEWS.find((x) => x === s.view),
    v: typeof s.v === 'number' ? s.v : undefined,
    p: typeof s.p === 'number' ? s.p : undefined,
  }),
  component: PageRoute,
})
```

Replace `PageRoute` with:

```tsx
function PageRoute() {
  const { _splat = '' } = Route.useParams()
  const { view } = Route.useSearch()
  const { data: page, isError } = usePage(pagePath(_splat))
  if (isError) return <p className="text-muted-foreground">Page not found.</p>
  if (!page) return null

  if (view === 'edit') return <PageEditor key={page.path} page={page} />

  return (
    <article>
      <PageActions page={page} />
      <PageView page={page}>
        {page.type === 'universe' && <UniverseMembers universe={page.path} />}
      </PageView>
    </article>
  )
}

function PageActions({ page }: { page: Page }) {
  const params = { _splat: pageSplat(page.path) }
  return (
    <nav aria-label="Page actions" className="mb-6 flex gap-4 text-sm">
      <Link to="/$" params={params} search={{ view: 'edit' }} className="hover:text-primary">
        Edit
      </Link>
      <Link to="/$" params={params} search={{ view: 'history' }} className="hover:text-primary">
        History
      </Link>
    </nav>
  )
}
```

- [ ] **Step 5: Run tests + typecheck**

Run: `npm run test && npm run typecheck`
Expected: PASS (including the existing `app.test.tsx`)

- [ ] **Step 6: Commit**

```bash
git add 'src/routes/$.tsx' src/components/PageEditor.tsx src/test/edit.test.tsx
git commit -m "feat: page editor with template check [#92]"
```

---

### Task 4: History list and read-only Version view (`?view=history[&v=]`)

**Files:**
- Create: `frontend/src/components/PageHistory.tsx`
- Modify: `frontend/src/routes/$.tsx` (one view branch)
- Test: `frontend/src/test/edit.test.tsx` (append)

**Interfaces:**
- Consumes: `useVersions(path)` (existing), `PageView` (existing), search `v` (Task 3)
- Produces: `PageHistory({ page, versionId }: { page: Page; versionId?: number })`; `<ol aria-label="Versions">` with one `<li>` per Version, each with a `View` link

- [ ] **Step 1: Write the failing tests** (append to `src/test/edit.test.tsx`)

```tsx
const versionRows = async () =>
  within(await screen.findByRole('list', { name: 'Versions' })).getAllByRole('listitem')

test('an edit appears on top of history', async () => {
  renderApp('/books/krew-elfow?view=edit')
  edit(await source(), (v) => v.replace('## Wątki i motywy', '## Wątki i motywy\n\nDopisek z edycji.'))
  fireEvent.click(screen.getByRole('button', { name: 'Save' }))
  await screen.findByText('Dopisek z edycji.')
  fireEvent.click(screen.getByRole('link', { name: 'History' }))
  const rows = await versionRows()
  expect(rows).toHaveLength(2)
  within(rows[0]).getByText('v2')
  within(rows[0]).getByText('Edit')
  within(rows[1]).getByText('Generation')
})

test('viewing an old version shows it read-only', async () => {
  renderApp('/books/ostatnie-zyczenie?view=history')
  const rows = await versionRows()
  expect(rows.map((r) => within(r).getByText(/^v\d+$/).textContent)).toEqual(['v3', 'v2', 'v1'])
  fireEvent.click(within(rows[2]).getByRole('link', { name: 'View' }))
  await screen.findByText(/Viewing v1 · Created/)
  screen.getByRole('heading', { level: 2, name: 'Streszczenie' })
  expect(screen.queryByText(/Ranny Geralt/)).toBeNull()
  expect(screen.queryByRole('link', { name: 'Edit' })).toBeNull()
})

test('an unknown version id shows not found', async () => {
  renderApp('/books/ostatnie-zyczenie?view=history&v=999')
  await screen.findByText('Version not found.')
})

test('an unknown view falls back to the page', async () => {
  renderApp('/books/ostatnie-zyczenie?view=bogus')
  await screen.findByRole('link', { name: 'Edit' })
})
```

- [ ] **Step 2: Run to verify they fail**

Run: `npx vitest run src/test/edit.test.tsx`
Expected: FAIL — no `Versions` list, no "Version not found."

- [ ] **Step 3: Create `src/components/PageHistory.tsx`**

```tsx
// Historia: every Version newest first; a picked Version renders read-only
import { Link } from '@tanstack/react-router'
import { useVersions } from '@/api/hooks'
import type { Page, VersionKind } from '@/api/types'
import { PageView } from '@/components/PageView'
import { pageSplat, parsePage } from '@/wiki'

const KIND_LABELS: Record<VersionKind, string> = {
  created: 'Created',
  generation: 'Generation',
  proposal: 'Proposal',
  edit: 'Edit',
}

const when = (iso: string) =>
  new Date(iso).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' })

export function PageHistory({ page, versionId }: { page: Page; versionId?: number }) {
  const { data: versions } = useVersions(page.path)
  if (!versions) return null
  const params = { _splat: pageSplat(page.path) }
  // Oldest is v1; ids are not contiguous, so number by position
  const label = (i: number) => `v${versions.length - i}`

  if (versionId !== undefined) {
    const i = versions.findIndex((v) => v.id === versionId)
    if (i === -1) return <p className="text-muted-foreground">Version not found.</p>
    const version = versions[i]
    const title = parsePage(version.content).frontmatter.title ?? page.title
    return (
      <article>
        <p className="mb-6 flex flex-wrap gap-3 rounded-md border bg-muted px-4 py-2 text-sm">
          <span className="font-semibold">
            Viewing {label(i)} · {KIND_LABELS[version.kind]} · {when(version.created_at)}
          </span>
          <Link to="/$" params={params} search={{ view: 'history' }} className="text-primary">
            History
          </Link>
          <Link to="/$" params={params} search={{}} className="text-primary">
            Back to current
          </Link>
        </p>
        <PageView page={{ ...page, content: version.content, title }} />
      </article>
    )
  }

  return (
    <section>
      <Link
        to="/$"
        params={params}
        search={{}}
        className="text-sm text-muted-foreground hover:text-primary"
      >
        ← {page.title}
      </Link>
      <h1 className="mt-2 font-heading text-3xl">History</h1>
      <ol aria-label="Versions" className="mt-6 divide-y rounded-md border">
        {versions.map((v, i) => (
          <li key={v.id} className="flex items-center gap-3 px-4 py-3 text-sm">
            <span className="font-mono text-muted-foreground">{label(i)}</span>
            <span className="rounded-full bg-muted px-2.5 py-0.5 text-xs font-semibold">
              {KIND_LABELS[v.kind]}
            </span>
            <span className="text-muted-foreground">
              {v.author} · {when(v.created_at)}
            </span>
            <Link
              to="/$"
              params={params}
              search={{ view: 'history', v: v.id }}
              className="ml-auto text-primary"
            >
              View
            </Link>
          </li>
        ))}
      </ol>
      <p className="mt-3 text-sm text-muted-foreground">
        Rejected proposals don&apos;t create versions.
      </p>
    </section>
  )
}
```

- [ ] **Step 4: Wire the view** in `src/routes/$.tsx`

Add the import:

```tsx
import { PageHistory } from '@/components/PageHistory'
```

In `PageRoute`, read `v` too and add the branch under the `edit` one:

```tsx
  const { view, v } = Route.useSearch()
```

```tsx
  if (view === 'history') return <PageHistory page={page} versionId={v} />
```

- [ ] **Step 5: Run tests + typecheck**

Run: `npm run test && npm run typecheck`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add 'src/routes/$.tsx' src/components/PageHistory.tsx src/test/edit.test.tsx
git commit -m "feat: version history and version view [#92]"
```

---

### Task 5: Proposal review with diff, accept/reject, stale (`?view=proposal&p=`)

**Files:**
- Modify: `frontend/package.json`, `frontend/package-lock.json` (`diff`)
- Create: `frontend/src/components/ProposalView.tsx`
- Modify: `frontend/src/routes/$.tsx` (one view branch, `OpenProposals` note)
- Test: `frontend/src/test/proposal.test.tsx`

**Interfaces:**
- Consumes: `useProposals(path)`, `useVersions(path)` (existing), `useAcceptProposal(path)`, `useRejectProposal(path)` (Task 2), `savePage`, `getPage` (Task 2, in tests), search `p` (Task 3)
- Produces: `ProposalView({ page, proposalId }: { page: Page; proposalId: number })`; on the page view, one note per open/stale Proposal: `Proposal: <prompt>` + link `Review`

- [ ] **Step 1: Install jsdiff**

Run: `npm install diff`
Expected: `diff` (^9) appears under `dependencies`; it ships its own types

- [ ] **Step 2: Write the failing tests** — create `src/test/proposal.test.tsx`

```tsx
import { fireEvent, screen, within } from '@testing-library/react'
import { getPage, savePage } from '@/api/store'
import { renderApp } from './renderApp'

const OZ = '/books/ostatnie-zyczenie.md'
const REVIEW = '/books/ostatnie-zyczenie?view=proposal&p=1'

const versionRows = async () =>
  within(await screen.findByRole('list', { name: 'Versions' })).getAllByRole('listitem')

test('the page links to its open proposal, which shows the diff', async () => {
  renderApp('/books/ostatnie-zyczenie')
  await screen.findByText(/Proposal: Dodaj Nivellena do postaci/)
  fireEvent.click(screen.getByRole('link', { name: 'Review' }))
  await screen.findByText('Dodaj Nivellena do postaci')
  screen.getByText(/^\+ - \[Nivellen\]/)
})

test('accept adds a proposal version and a verified event', async () => {
  renderApp(REVIEW)
  fireEvent.click(await screen.findByRole('button', { name: /^Accept/ }))
  await screen.findByText('Nivellen')
  screen.getByText(/verified by human:stokuj, human:stokuj/)
  expect(screen.queryByText(/Proposal: Dodaj Nivellena/)).toBeNull()
  fireEvent.click(screen.getByRole('link', { name: 'History' }))
  const rows = await versionRows()
  expect(rows).toHaveLength(4)
  within(rows[0]).getByText('Proposal')
})

test('reject leaves the page and history unchanged', async () => {
  const before = getPage(OZ).content
  renderApp(REVIEW)
  fireEvent.click(await screen.findByRole('button', { name: 'Reject' }))
  await screen.findByRole('link', { name: 'History' })
  expect(screen.queryByText(/Proposal: Dodaj Nivellena/)).toBeNull()
  expect(getPage(OZ).content).toBe(before)
  fireEvent.click(screen.getByRole('link', { name: 'History' }))
  expect(await versionRows()).toHaveLength(3)
})

test('after an edit the proposal is stale and accept is disabled', async () => {
  savePage(OZ, getPage(OZ).content + '\nDopisek.\n')
  renderApp(REVIEW)
  const accept = (await screen.findByRole('button', { name: /^Accept/ })) as HTMLButtonElement
  expect(accept.disabled).toBe(true)
  screen.getByText('This page changed since the proposal was made.')
  expect(screen.queryByRole('button', { name: 'Reject' })).toBeNull()
})
```

- [ ] **Step 3: Run to verify they fail**

Run: `npx vitest run src/test/proposal.test.tsx`
Expected: FAIL — no "Proposal: …" note, no `Accept` button

- [ ] **Step 4: Create `src/components/ProposalView.tsx`**

```tsx
// Propozycja: line diff against its base Version; accept/reject, accept blocked when stale
import { Link, useNavigate } from '@tanstack/react-router'
import { diffLines } from 'diff'
import { useAcceptProposal, useProposals, useRejectProposal, useVersions } from '@/api/hooks'
import type { Page } from '@/api/types'
import { pageSplat } from '@/wiki'

const button = 'rounded-md px-4 py-1.5 text-sm font-semibold disabled:opacity-50'

export function ProposalView({ page, proposalId }: { page: Page; proposalId: number }) {
  const { data: proposals } = useProposals(page.path)
  const { data: versions } = useVersions(page.path)
  const accept = useAcceptProposal(page.path)
  const reject = useRejectProposal(page.path)
  const navigate = useNavigate()
  if (!proposals || !versions) return null

  const proposal = proposals.find((p) => p.id === proposalId)
  if (!proposal) return <p className="text-muted-foreground">Proposal not found.</p>
  const base = versions.find((v) => v.id === proposal.base_version)
  const params = { _splat: pageSplat(page.path) }
  const back = () => navigate({ to: '/$', params, search: {} })
  const error = accept.error ?? reject.error

  return (
    <section>
      <Link
        to="/$"
        params={params}
        search={{}}
        className="text-sm text-muted-foreground hover:text-primary"
      >
        ← {page.title}
      </Link>
      <h1 className="mt-2 font-heading text-3xl">Proposal from the Agent</h1>
      <div className="mt-6 rounded-md border bg-muted px-4 py-3">
        <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
          You asked
        </p>
        <p className="mt-1">{proposal.prompt}</p>
      </div>

      <Diff before={base?.content ?? ''} after={proposal.content} />

      {error && (
        <p role="alert" className="mt-2 text-sm text-destructive">
          {error.message}
        </p>
      )}

      {proposal.status === 'open' && (
        <div className="mt-4 flex gap-2">
          <button
            type="button"
            disabled={accept.isPending}
            onClick={() => accept.mutate(proposal.id, { onSuccess: back })}
            className={`${button} bg-primary text-primary-foreground`}
          >
            Accept → new version v{versions.length + 1}
          </button>
          <button
            type="button"
            disabled={reject.isPending}
            onClick={() => reject.mutate(proposal.id, { onSuccess: back })}
            className={`${button} border`}
          >
            Reject
          </button>
        </div>
      )}

      {proposal.status === 'stale' && (
        <div className="mt-4 space-y-2">
          <p className="text-sm">This page changed since the proposal was made.</p>
          <div className="flex items-center gap-2">
            <button type="button" disabled className={`${button} bg-primary text-primary-foreground`}>
              Accept → new version v{versions.length + 1}
            </button>
            <button type="button" disabled className={`${button} border`}>
              Regenerate
            </button>
            <span className="text-sm text-muted-foreground">Agent arrives in M3</span>
          </div>
        </div>
      )}

      {(proposal.status === 'accepted' || proposal.status === 'rejected') && (
        <p className="mt-4">
          <span className="rounded-full bg-muted px-2.5 py-0.5 text-xs font-semibold">
            {proposal.status}
          </span>
        </p>
      )}
    </section>
  )
}

function Diff({ before, after }: { before: string; after: string }) {
  const lines = diffLines(before, after).flatMap((part) =>
    part.value
      .replace(/\n$/, '')
      .split('\n')
      .map((text) => ({ text, added: part.added, removed: part.removed })),
  )
  return (
    <pre className="mt-6 overflow-x-auto rounded-md border p-3 font-mono text-sm whitespace-pre-wrap">
      {lines.map((l, i) => (
        <div
          key={i}
          className={
            l.added ? 'bg-green-50 text-green-900' : l.removed ? 'bg-red-50 text-red-900' : undefined
          }
        >
          {l.added ? '+ ' : l.removed ? '− ' : '  '}
          {l.text}
        </div>
      ))}
    </pre>
  )
}
```

- [ ] **Step 5: Wire the view and the note** in `src/routes/$.tsx`

Extend the imports:

```tsx
import { usePage, usePages, useProposals } from '@/api/hooks'
import { ProposalView } from '@/components/ProposalView'
```

In `PageRoute`, read `p` and add the branch under the `history` one:

```tsx
  const { view, v, p } = Route.useSearch()
```

```tsx
  if (view === 'proposal' && p !== undefined) return <ProposalView page={page} proposalId={p} />
```

Render the note under `<PageActions page={page} />`:

```tsx
      <PageActions page={page} />
      <OpenProposals page={page} />
```

Add the component:

```tsx
function OpenProposals({ page }: { page: Page }) {
  const { data: proposals = [] } = useProposals(page.path)
  const pending = proposals.filter((p) => p.status === 'open' || p.status === 'stale')
  if (pending.length === 0) return null
  return (
    <ul className="mb-6 space-y-2">
      {pending.map((p) => (
        <li key={p.id} className="rounded-md border bg-muted px-4 py-2 text-sm">
          Proposal: {p.prompt}{' '}
          <Link
            to="/$"
            params={{ _splat: pageSplat(page.path) }}
            search={{ view: 'proposal', p: p.id }}
            className="font-semibold text-primary"
          >
            Review
          </Link>
        </li>
      ))}
    </ul>
  )
}
```

- [ ] **Step 6: Run tests + typecheck + lint**

Run: `npm run test && npm run typecheck && npm run lint`
Expected: PASS, no errors

- [ ] **Step 7: Commit**

```bash
git add package.json package-lock.json 'src/routes/$.tsx' src/components/ProposalView.tsx src/test/proposal.test.tsx
git commit -m "feat: proposal diff, accept and reject [#92]"
```

---

### Task 6: Profile screen and sidebar link

**Files:**
- Create: `frontend/src/routes/profile.tsx`
- Modify: `frontend/src/components/Sidebar.tsx` (profile link at the bottom of the nav)
- Modify: `frontend/src/routeTree.gen.ts` (regenerated)
- Test: `frontend/src/test/profile.test.tsx`

**Interfaces:**
- Consumes: `useProfile()` (existing), `useSetProfilePublic()` (Task 2)
- Produces: route `/profile`; sidebar link named `@<handle>`

- [ ] **Step 1: Write the failing tests** — create `src/test/profile.test.tsx`

```tsx
import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { renderApp } from './renderApp'

const cards = (name: string) =>
  within(screen.getByRole('heading', { name }).closest('section')!).getAllByRole('listitem')

test('profile shows about, the public switch and favourite cards', async () => {
  renderApp('/')
  fireEvent.click(await screen.findByRole('link', { name: '@stokuj' }))
  await screen.findByRole('heading', { level: 1, name: '@stokuj' })
  screen.getByText('Czytam fantastykę, głównie polską.')
  expect(cards('Favourite books')).toHaveLength(2)
  expect(cards('Favourite characters')).toHaveLength(1)
  screen.getByText('Wiedźmin, łowca potworów ze szkoły Wilka.')
  expect(within(screen.getByRole('main')).queryAllByRole('link')).toHaveLength(0)
})

test('the public switch toggles visibility', async () => {
  renderApp('/profile')
  const toggle = (await screen.findByRole('switch', { name: 'Public profile' })) as HTMLInputElement
  expect(toggle.checked).toBe(true)
  fireEvent.click(toggle)
  await waitFor(() => expect(toggle.checked).toBe(false))
})
```

- [ ] **Step 2: Run to verify they fail**

Run: `npx vitest run src/test/profile.test.tsx`
Expected: FAIL — no `@stokuj` link; `/profile` falls into the splat route ("Page not found.")

- [ ] **Step 3: Create `src/routes/profile.tsx`**

```tsx
import { createFileRoute } from '@tanstack/react-router'
import { useProfile, useSetProfilePublic } from '@/api/hooks'
import type { Profile } from '@/api/types'

export const Route = createFileRoute('/profile')({
  component: ProfilePage,
})

function ProfilePage() {
  const { data: profile } = useProfile()
  const setPublic = useSetProfilePublic()
  if (!profile) return null
  // Ulubione are book or character Pages; the Path prefix tells which
  const favorites = (prefix: string) => profile.favorites.filter((f) => f.path.startsWith(prefix))

  return (
    <section className="max-w-2xl">
      <header className="flex items-center gap-4">
        <span
          aria-hidden
          className="grid size-14 place-items-center rounded-full bg-primary text-lg font-semibold text-primary-foreground"
        >
          {profile.handle.slice(0, 2).toUpperCase()}
        </span>
        <h1 className="font-heading text-3xl">@{profile.handle}</h1>
        <label className="ml-auto flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            role="switch"
            checked={profile.is_public}
            onChange={(e) => setPublic.mutate(e.target.checked)}
          />
          Public profile
        </label>
      </header>

      <h2 className="mt-8 font-heading text-xl">About me</h2>
      <p className="mt-2">{profile.about}</p>

      <Favorites title="Favourite books" items={favorites('/books/')} />
      <Favorites title="Favourite characters" items={favorites('/characters/')} />

      <p className="mt-10 text-sm text-muted-foreground">
        Visitors see these as cards only. Your wiki pages stay private.
      </p>
    </section>
  )
}

// Cards only (title + description), no link: CONTEXT — visitors never reach the Page
function Favorites({ title, items }: { title: string; items: Profile['favorites'] }) {
  if (items.length === 0) return null
  return (
    <section className="mt-8">
      <h2 className="font-heading text-xl">{title}</h2>
      <ul className="mt-3 grid grid-cols-2 gap-3">
        {items.map((f) => (
          <li key={f.path} className="rounded-md border p-4">
            <p className="font-semibold">{f.title}</p>
            <p className="mt-1 text-sm text-muted-foreground">{f.description}</p>
          </li>
        ))}
      </ul>
    </section>
  )
}
```

- [ ] **Step 4: Add the profile link** to `src/components/Sidebar.tsx`

Import `useProfile` alongside `usePages` from `@/api/hooks`, call it at the top of `Sidebar`:

```tsx
  const { data: profile } = useProfile()
```

and render as the last child of `<nav>` (after the `SECTIONS.map(...)` block):

```tsx
      {profile && (
        <Link
          to="/profile"
          className="mt-auto rounded-md px-2 py-1 text-sm text-muted-foreground hover:bg-background"
          activeProps={{ className: 'bg-background font-medium text-primary' }}
        >
          @{profile.handle}
        </Link>
      )}
```

- [ ] **Step 5: Regenerate the route tree**

Run: `npm run build`
Expected: build succeeds; `git status` shows `src/routeTree.gen.ts` modified with a `/profile` route

- [ ] **Step 6: Run tests + typecheck + lint + format check**

Run: `npm run test && npm run typecheck && npm run lint && npm run format:check`
Expected: PASS. If `format:check` fails, run `npm run format` and re-run.

- [ ] **Step 7: Commit**

```bash
git add src/routes/profile.tsx src/components/Sidebar.tsx src/routeTree.gen.ts src/test/profile.test.tsx
git commit -m "feat: profile screen with favourite cards [#92]"
```

---

### Task 7: Full verification

- [ ] **Step 1: Format everything touched under `frontend/`**

Run: `npm run format && git status --short`
Expected: no unexpected changes (commit any formatting fix as `style: format [#92]`)

- [ ] **Step 2: CI-equivalent gate** (from the worktree root; needs the dev DB per `CLAUDE.md`)

Run: `make verify ENV_FILE=/home/dv6/GitHub/storyshelf/infra/.env`
Expected: lint + backend tests + frontend typecheck/lint/test/build all PASS

- [ ] **Step 3: Route tree is committed**

Run: `git diff --exit-code src/routeTree.gen.ts` (from `frontend/`)
Expected: exit 0
