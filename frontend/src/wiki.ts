// Pure helpers over wiki Pages: URL ↔ Path, grouping, universe membership, OKF parsing
import { parse } from 'yaml'
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
