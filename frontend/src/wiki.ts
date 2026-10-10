// Pure helpers over wiki Pages: URL ↔ Path, grouping, universe membership, OKF parsing
import { isSeq, parse, parseDocument } from 'yaml'
import type { PageSummary, PageType } from './api/types'

// Path '/books/x.md' ↔ splat 'books/x' (URL '/books/x')
export const pageSplat = (path: string) => path.slice(1).replace(/\.md$/, '')
// Tolerates a trailing '/' and a missing or present '.md': 'books/x/' → '/books/x.md'
export const pagePath = (splat: string) =>
  `/${splat.replace(/\/+$/, '').replace(/(\.md)?$/, '.md')}`

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

export function groupByType(pages: PageSummary[]): Record<PageType, PageSummary[]> {
  const groups: Record<PageType, PageSummary[]> = {
    book: [],
    character: [],
    place: [],
    universe: [],
  }
  for (const p of pages) groups[p.type].push(p)
  return groups
}

// Characters and places belong to a universe through their book (CONTEXT: per book for now)
export function universeMembers(pages: PageSummary[], universe: string) {
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

// Optional BOM, opening `---`, optional YAML block, closing `---`; LF or CRLF
const FRONTMATTER = /^\uFEFF?---\r?\n(?:([\s\S]*?)\r?\n)?---(?:\r?\n|$)/

export function parsePage(content: string): { frontmatter: Frontmatter; body: string } {
  const match = FRONTMATTER.exec(content)
  if (!match) throw new Error('Missing frontmatter')
  return {
    frontmatter: (parse(match[1] ?? '') ?? {}) as Frontmatter,
    body: content.slice(match[0].length).trimStart(),
  }
}

// Kept for the M3 Proposal flow (only tests use it now)
// Appends a Weryfikacja event (OKF v0.2 §5.2) without reformatting the rest of the frontmatter
export function addVerified(content: string, by: string, at: string): string {
  const match = FRONTMATTER.exec(content)
  if (!match) throw new Error('Missing frontmatter')
  const doc = parseDocument(match[1] ?? '')
  if (doc.errors.length) throw new Error(`Invalid frontmatter: ${doc.errors[0].message}`)
  const event = { by, at }
  const list = doc.get('verified')
  if (isSeq(list)) list.add(doc.createNode(event))
  else doc.set('verified', doc.createNode([event]))
  const eol = match[0].includes('\r\n') ? '\r\n' : '\n'
  const yaml = String(doc).replaceAll('\n', eol)
  return `---${eol}${yaml}---${eol}${content.slice(match[0].length)}`
}
