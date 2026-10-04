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
