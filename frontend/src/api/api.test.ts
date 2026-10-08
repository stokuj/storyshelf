import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { createElement, type ReactNode } from 'react'
import { usePage } from './hooks'
import { parsePage, validateEdit } from '@/wiki'
import {
  acceptProposal,
  createBook,
  generatePage,
  getPage,
  getProfile,
  listPages,
  listProposals,
  listVersions,
  rejectProposal,
  resetStore,
  savePage,
  searchCandidates,
  setProfilePublic,
} from './store'

const TYPE_DIRS = {
  book: '/books/',
  character: '/characters/',
  place: '/places/',
  universe: '/universes/',
}

function wrapper({ children }: { children: ReactNode }) {
  return createElement(QueryClientProvider, { client: new QueryClient() }, children)
}

test('usePage returns a book page with a character mention', async () => {
  const { result } = renderHook(() => usePage('/books/ostatnie-zyczenie.md'), { wrapper })
  await waitFor(() => expect(result.current.isSuccess).toBe(true))
  expect(result.current.data?.type).toBe('book')
  expect(result.current.data?.content).toMatch(/\]\(\/characters\/[^)]+\.md\)/)
})

test('every fixture has a valid type matching its directory', () => {
  const pages = listPages()
  expect(pages.length).toBeGreaterThan(0)
  for (const page of pages) {
    expect(Object.keys(TYPE_DIRS)).toContain(page.type)
    expect(page.path.startsWith(TYPE_DIRS[page.type])).toBe(true)
  }
})

test('book and universe fields point to existing pages', () => {
  const pages = listPages()
  const paths = new Set(pages.map((p) => p.path))
  for (const page of pages) {
    if (page.book) expect(paths).toContain(page.book)
    if (page.universe) expect(paths).toContain(page.universe)
  }
})

test('recorded history and proposal differ from current content', () => {
  const [v3, v2] = listVersions('/books/ostatnie-zyczenie.md')
  expect(v2.content).not.toBe(v3.content)
  expect(v2.content).not.toContain('verified:')
  expect(listProposals('/books/ostatnie-zyczenie.md')[0].content).not.toBe(v3.content)
})

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
  const [a, b] = [retitle('A'), retitle('B')]
  vi.useFakeTimers({ now: new Date('2026-10-05T10:00:00Z') })
  savePage(KE, a)
  savePage(KE, b)
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
