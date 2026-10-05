// Pure helpers over wiki Pages: URL ↔ Path, grouping, universe membership, OKF parsing
import { isSeq, parse, parseDocument } from 'yaml'
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
