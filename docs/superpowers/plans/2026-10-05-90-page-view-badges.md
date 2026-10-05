# Wiki page view with mention badges Implementation Plan (#90)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A wiki Page renders like the mockups: frontmatter header, Markdown body, sources/verification footer, and every link to a character or place page as a coloured badge; links to missing pages render as plain text.

**Architecture:** `parsePage` in `src/wiki.ts` splits raw `.md` into frontmatter + body (the fake store reuses it). `src/components/PageView.tsx` renders header, body via `react-markdown`, footer. A custom `a` renderer (`WikiLink`) classifies every link by its Path prefix and checks existence against the `usePages()` list. `routes/$.tsx` swaps its title stub for `<PageView>`.

**Tech Stack:** React 19, TanStack Router + Query, `react-markdown` (new), `yaml`, Tailwind v4 tokens in `index.css`, Vitest + Testing Library.

**Spec:** `docs/superpowers/specs/2026-10-05-90-page-view-badges.md`

## Global Constraints

- Character badge `#F8E9DF` / `#6B2C12`; place badge `#E4EDF7` / `#1F4A7A` (tokens `--character`, `--place` in `:root`)
- Only new dependency: `react-markdown`. No `lucide-react`, no `@tailwindcss/typography`
- Internal link = `href` starts with `/`; existence = Path present in `usePages()` data
- Missing `status` → no pill; empty footer → no footer
- UI labels in English (like the mockups)
- `.dark` block untouched
- All commands run from `frontend/`; `make verify` from repo root before PR
- Commit titles ≤ 50 chars, conventional commits, no `Co-Authored-By`

## Review Focus

1. Link to a missing Page (Nenneke) → plain text, no crash, no `<a>` — test in Task 3
2. Clicking a badge while on a Page → URL and content switch to the target Page (same splat route, new param) — test in Task 3 (h1 becomes "Renfri")
3. Draft Page with empty sections and no `generated`/`sources`/`verified` (Snaut) → header with `draft` pill, no footer, no crash — test in Task 2
4. Internal link to a book/universe Page → plain `<Link>`, not a badge — fixture link added to `wiedzmin.md`, test in Task 3
5. External link (`https://…`) in body or sources → opens in new tab with `rel="noopener noreferrer"`, never treated as a wiki Path — tests in Task 2 (footer) and Task 3 (body)

---

### Task 0: Worktree setup

- [ ] **Step 1: Install dependencies** (the worktree has no `node_modules`)

Run: `npm ci`
Expected: completes without errors

- [ ] **Step 2: Baseline**

Run: `npm run test`
Expected: all existing tests PASS

---

### Task 1: `parsePage` in `wiki.ts`, reused by the store

**Files:**
- Modify: `frontend/src/wiki.ts`
- Modify: `frontend/src/api/store.ts:1-25` (drop local `Frontmatter` + `parseFrontmatter`, import `parsePage`)
- Test: `frontend/src/wiki.test.ts`

**Interfaces:**
- Produces: `interface Frontmatter`, `parsePage(content: string): { frontmatter: Frontmatter; body: string }` exported from `@/wiki`

- [ ] **Step 1: Write the failing tests** (append to `src/wiki.test.ts`, extend the import)

```ts
import { getPage, listPages } from '@/api/store'
import { groupByType, pagePath, pageSplat, parsePage, universeMembers } from '@/wiki'
```

```ts
test('parsePage splits frontmatter from body', () => {
  const { frontmatter, body } = parsePage(getPage('/books/ostatnie-zyczenie.md').content)
  expect(frontmatter.type).toBe('book')
  expect(frontmatter.verified?.[0].by).toBe('human:stokuj')
  expect(body.startsWith('## Streszczenie')).toBe(true)
})

test('parsePage rejects content without frontmatter', () => {
  expect(() => parsePage('## Just a body')).toThrow('Missing frontmatter')
})
```

- [ ] **Step 2: Run to verify they fail**

Run: `npx vitest run src/wiki.test.ts`
Expected: FAIL — `parsePage` is not exported

- [ ] **Step 3: Implement in `src/wiki.ts`**

Add to the imports and below the existing helpers:

```ts
import { parse } from 'yaml'
```

```ts
// OKF frontmatter fields the UI reads (raw content stays the source of truth)
export interface Frontmatter {
  type: PageType
  title?: string
  description?: string
  author?: string
  status?: string
  book?: string
  universe?: string
  sources?: { id: string; resource?: string; title?: string }[]
  generated?: { by: string; at: string }
  verified?: { by: string; at: string }[]
}

export function parsePage(content: string): { frontmatter: Frontmatter; body: string } {
  const match = /^---\n([\s\S]*?)\n---\n?/.exec(content)
  if (!match) throw new Error('Missing frontmatter')
  return {
    frontmatter: parse(match[1]) as Frontmatter,
    body: content.slice(match[0].length).trimStart(),
  }
}
```

Update the top comment of `wiki.ts` to: `// Pure helpers over wiki Pages: URL ↔ Path, grouping, universe membership, OKF parsing`

- [ ] **Step 4: Reuse it in `src/api/store.ts`**

Delete `import { parse } from 'yaml'`, the `interface Frontmatter { … }` block and `function parseFrontmatter(…) { … }`. Add `import { parsePage } from '@/wiki'` and change the loop line to:

```ts
  const fm = parsePage(content).frontmatter
```

- [ ] **Step 5: Run tests and typecheck**

Run: `npm run test && npm run typecheck`
Expected: PASS (existing store/sidebar tests prove the refactor kept behaviour)

- [ ] **Step 6: Commit**

```bash
git add src/wiki.ts src/wiki.test.ts src/api/store.ts
git commit -m "refactor: move parsePage to wiki.ts [#90]"
```

---

### Task 2: `PageView` — header, Markdown body, footer

**Files:**
- Modify: `frontend/package.json`, `frontend/package-lock.json` (via npm)
- Modify: `frontend/src/index.css` (badge tokens + `.page-body` styles)
- Create: `frontend/src/components/PageView.tsx`
- Modify: `frontend/src/routes/$.tsx:10-24`
- Test: `frontend/src/test/app.test.tsx`

**Interfaces:**
- Consumes: `parsePage`, `Frontmatter` from `@/wiki` (Task 1); `Page` from `@/api/types`
- Produces: `PageView({ page, children }: { page: Page; children?: ReactNode })` — children render between body and footer. Task 3 adds `WikiLink` to the same file and passes it as `components.a`.

- [ ] **Step 1: Write the failing tests** (append to `src/test/app.test.tsx`)

```ts
test.each([
  ['/books/ostatnie-zyczenie', 'Ostatnie życzenie'],
  ['/characters/renfri--ostatnie-zyczenie', 'Renfri'],
  ['/places/blaviken--ostatnie-zyczenie', 'Blaviken'],
  ['/universes/wiedzmin', 'Wiedźmin'],
])('%s renders header and body', async (url, title) => {
  renderApp(url)
  const main = await screen.findByRole('main')
  await within(main).findByRole('heading', { level: 1, name: title })
  expect(within(main).getAllByRole('heading', { level: 2 }).length).toBeGreaterThan(0)
})

test('book footer shows sources and verification', async () => {
  renderApp('/books/ostatnie-zyczenie')
  const footer = await screen.findByRole('contentinfo')
  const source = within(footer).getByRole('link', { name: 'Ostatnie życzenie — Wikipedia' })
  expect(source.getAttribute('target')).toBe('_blank')
  expect(source.getAttribute('rel')).toBe('noopener noreferrer')
  within(footer).getByText(/human:stokuj/)
  expect(within(screen.getByRole('main')).queryByText('draft')).toBeNull()
})

test('draft page shows its status and no footer', async () => {
  renderApp('/characters/snaut--solaris')
  const main = await screen.findByRole('main')
  await within(main).findByRole('heading', { level: 1, name: 'Snaut' })
  within(main).getByText('draft')
  expect(within(main).queryByRole('contentinfo')).toBeNull()
})
```

Note: a `<footer>` inside `<main>` has no implicit `contentinfo` role, so Step 5 sets `role="contentinfo"` explicitly.

- [ ] **Step 2: Run to verify they fail**

Run: `npx vitest run src/test/app.test.tsx`
Expected: FAIL — no level-2 headings, no footer, no `draft`

- [ ] **Step 3: Install `react-markdown`**

Run: `npm install react-markdown`
Expected: added to `dependencies` in `package.json`

- [ ] **Step 4: Tokens and body styles in `src/index.css`**

Inside `@theme inline { … }` add:

```css
  --color-character: var(--character);
  --color-character-foreground: var(--character-foreground);
  --color-place: var(--place);
  --color-place-foreground: var(--place-foreground);
```

Inside `:root { … }` add:

```css
  --character: #f8e9df;
  --character-foreground: #6b2c12;
  --place: #e4edf7;
  --place-foreground: #1f4a7a;
```

At the end of the file add:

```css
/* Rendered Markdown body of a wiki Page (no typography plugin) */
.page-body h2 {
  @apply mt-8 mb-3 font-heading text-2xl font-semibold;
}
.page-body p {
  @apply mb-4 leading-relaxed;
}
.page-body ul {
  @apply mb-4 list-disc space-y-2 pl-5;
}
```

- [ ] **Step 5: Create `src/components/PageView.tsx`**

```tsx
// One wiki Page: frontmatter header, Markdown body, sources/verification footer
import type { ReactNode } from 'react'
import Markdown from 'react-markdown'
import type { Page } from '@/api/types'
import { parsePage } from '@/wiki'

export function PageView({ page, children }: { page: Page; children?: ReactNode }) {
  const { frontmatter: fm, body } = parsePage(page.content)
  const verifiers = (fm.verified ?? []).map((v) => v.by)
  const hasFooter = Boolean(fm.sources?.length || fm.generated || verifiers.length)

  return (
    <>
      <header>
        <p className="font-mono text-xs text-muted-foreground">{page.path}</p>
        <h1 className="mt-1 font-heading text-4xl">{page.title}</h1>
        <p className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
          <span>{page.type}</span>
          {fm.author && <span>· {fm.author}</span>}
          {fm.status && (
            <span className="rounded-full bg-muted px-2.5 py-0.5 text-xs font-semibold text-foreground">
              {fm.status}
            </span>
          )}
        </p>
        {fm.description && <p className="mt-3 text-lg text-muted-foreground">{fm.description}</p>}
      </header>

      <div className="page-body mt-6">
        <Markdown>{body}</Markdown>
      </div>

      {children}

      {hasFooter && (
        <footer
          role="contentinfo"
          className="mt-10 flex flex-wrap gap-x-4 gap-y-1.5 border-t pt-4 text-[13px] text-muted-foreground"
        >
          {fm.sources?.length ? (
            <span>
              Sources:{' '}
              {fm.sources.map((s, i) => (
                <span key={s.id}>
                  {i > 0 && ', '}
                  {s.resource ? (
                    <a href={s.resource} target="_blank" rel="noopener noreferrer" className="underline">
                      {s.title ?? s.id}
                    </a>
                  ) : (
                    (s.title ?? s.id)
                  )}
                </span>
              ))}
            </span>
          ) : null}
          {fm.generated && <span>Generated by {fm.generated.by}</span>}
          {verifiers.length > 0 && <span>verified by {verifiers.join(', ')}</span>}
        </footer>
      )}
    </>
  )
}
```

- [ ] **Step 6: Use it in `src/routes/$.tsx`**

Replace the `// ponytail: title + Path only; …` comment and the returned `<article>` with:

```tsx
  return (
    <article>
      <PageView page={page}>
        {page.type === 'universe' && <UniverseMembers universe={page.path} />}
      </PageView>
    </article>
  )
```

Add `import { PageView } from '@/components/PageView'`. Leave `UniverseMembers` and `PageList` unchanged.

- [ ] **Step 7: Run tests, typecheck, lint, format**

Run: `npm run test && npm run typecheck && npm run lint && npm run format:check`
Expected: PASS (if `format:check` fails, run `npm run format` and re-check)

- [ ] **Step 8: Commit**

```bash
git add package.json package-lock.json src/index.css src/components/PageView.tsx src/routes/\$.tsx src/test/app.test.tsx
git commit -m "feat: render wiki page header, body, footer [#90]"
```

---

### Task 3: `WikiLink` — mention badges and missing links

**Files:**
- Modify: `frontend/src/components/PageView.tsx`
- Modify: `frontend/src/api/fixtures/universes/wiedzmin.md` (add a book link and an external link to the body)
- Test: `frontend/src/test/app.test.tsx`

**Interfaces:**
- Consumes: `PageView` (Task 2), `usePages` from `@/api/hooks`, `pageSplat` from `@/wiki`
- Produces: `WikiLink` (module-private), passed as `<Markdown components={{ a: WikiLink }}>`

- [ ] **Step 1: Extend the universe fixture**

Append to the end of `src/api/fixtures/universes/wiedzmin.md`:

```md

Saga zaczyna się od [Ostatniego życzenia](/books/ostatnie-zyczenie.md). Więcej w [Wikipedii](https://pl.wikipedia.org/wiki/Wiedźmin).
```

- [ ] **Step 2: Write the failing tests** (append to `src/test/app.test.tsx`)

```ts
test('mentions render as badges by page type', async () => {
  renderApp('/books/ostatnie-zyczenie')
  const body = (await screen.findByRole('heading', { level: 2, name: 'Postacie' })).closest('.page-body') as HTMLElement
  for (const name of ['Geralt z Rivii', 'Jaskier', 'Yennefer z Vengerbergu', 'Renfri']) {
    expect(within(body).getByRole('link', { name }).className).toContain('bg-character')
  }
  expect(within(body).getByRole('link', { name: 'Blaviken' }).className).toContain('bg-place')
})

test('clicking a badge opens that page', async () => {
  const router = renderApp('/books/ostatnie-zyczenie')
  const main = await screen.findByRole('main')
  fireEvent.click(await within(main).findByRole('link', { name: 'Renfri' }))
  await waitFor(() =>
    expect(router.state.location.pathname).toBe('/characters/renfri--ostatnie-zyczenie'),
  )
  await within(main).findByRole('heading', { level: 1, name: 'Renfri' })
})

test('link to a missing page renders as plain text', async () => {
  renderApp('/books/ostatnie-zyczenie')
  const main = await screen.findByRole('main')
  await within(main).findByText('Nenneke')
  expect(within(main).queryByRole('link', { name: 'Nenneke' })).toBeNull()
})

test('book and external links in the body are plain links', async () => {
  renderApp('/universes/wiedzmin')
  const body = (await screen.findByRole('heading', { level: 2, name: 'Opis' })).closest('.page-body') as HTMLElement
  const book = within(body).getByRole('link', { name: 'Ostatniego życzenia' })
  expect(book.getAttribute('href')).toBe('/books/ostatnie-zyczenie')
  expect(book.className).not.toContain('bg-')
  const external = within(body).getByRole('link', { name: 'Wikipedii' })
  expect(external.getAttribute('target')).toBe('_blank')
  expect(external.getAttribute('rel')).toBe('noopener noreferrer')
})
```

- [ ] **Step 3: Run to verify they fail**

Run: `npx vitest run src/test/app.test.tsx`
Expected: FAIL — links have raw `.md` hrefs, no badge classes, Nenneke is a link

- [ ] **Step 4: Implement `WikiLink` in `src/components/PageView.tsx`**

Extend imports:

```tsx
import { Link } from '@tanstack/react-router'
import type { ComponentProps, ReactNode } from 'react'
import Markdown, { type ExtraProps } from 'react-markdown'
import { usePages } from '@/api/hooks'
import type { Page } from '@/api/types'
import { pageSplat, parsePage } from '@/wiki'
```

Change the body to `<Markdown components={{ a: WikiLink }}>{body}</Markdown>` and add below `PageView`:

```tsx
const badge = 'inline-flex items-center gap-1.5 rounded-full px-3 py-0.5 text-sm font-semibold'

// Odnośnik: character/place → badge, other wiki Path → link, missing Path → text (OKF tolerates broken links)
function WikiLink({ href = '', children }: ComponentProps<'a'> & ExtraProps) {
  const { data: pages = [] } = usePages()

  if (!href.startsWith('/')) {
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" className="text-primary underline">
        {children}
      </a>
    )
  }
  // ponytail: linear scan per link, fine for one user's wiki; build a Set in a hook if pages grow large
  if (!pages.some((p) => p.path === href)) return <span>{children}</span>

  const params = { _splat: pageSplat(href) }
  if (href.startsWith('/characters/')) {
    return (
      <Link to="/$" params={params} className={`${badge} bg-character text-character-foreground`}>
        <PersonIcon />
        {children}
      </Link>
    )
  }
  if (href.startsWith('/places/')) {
    return (
      <Link to="/$" params={params} className={`${badge} bg-place text-place-foreground`}>
        <PinIcon />
        {children}
      </Link>
    )
  }
  return (
    <Link to="/$" params={params} className="text-primary underline">
      {children}
    </Link>
  )
}

const iconProps = {
  width: 13,
  height: 13,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 2,
  'aria-hidden': true,
} as const

const PersonIcon = () => (
  <svg {...iconProps}>
    <circle cx="12" cy="8" r="4" />
    <path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6" />
  </svg>
)

const PinIcon = () => (
  <svg {...iconProps}>
    <path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z" />
    <circle cx="12" cy="10" r="2.5" />
  </svg>
)
```

Deviation from spec, on purpose: `pages.some(...)` instead of a `Set` — same result, no per-link Set rebuild, no extra hook. Marked with `ponytail:`.

- [ ] **Step 5: Run the full check**

Run: `npm run test && npm run typecheck && npm run lint && npm run format:check`
Expected: PASS (sidebar counts are unchanged: the fixture edit adds no Page)

- [ ] **Step 6: Commit**

```bash
git add src/components/PageView.tsx src/api/fixtures/universes/wiedzmin.md src/test/app.test.tsx
git commit -m "feat: mention badges and broken links [#90]"
```

---

### Task 4: Verify and finish

- [ ] **Step 1: Full gate from repo root**

Run: `make verify` (from the worktree root)
Expected: lint + tests green for backend and frontend

- [ ] **Step 2: Manual check**

Run: `npm run dev`, open `http://localhost:5173/books/ostatnie-zyczenie`
Expected: terracotta badges for 4 characters, blue for Blaviken, "Nenneke" as plain text, footer with Wikipedia source and `human:stokuj`

- [ ] **Step 3: Hand off** to review: code review subagent + `devkit:adr-guardian` in parallel, then `devkit:gh-pr` (PR → `dev`, title ends with `[#90]`)
