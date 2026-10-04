import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { createElement, type ReactNode } from 'react'
import { usePage } from './hooks'
import { listPages, listProposals, listVersions } from './store'

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
