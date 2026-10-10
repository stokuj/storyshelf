// Pure helpers over wiki Pages: URL ↔ Path, grouping, universe membership, OKF parsing
import { isSeq, parse, parseDocument } from 'yaml'
import type { Page, PageType } from './api/types'

// Path '/books/x.md' ↔ splat 'books/x' (URL '/books/x')
export const pageSplat = (path: string) => path.slice(1).replace(/\.md$/, '')
export const pagePath = (splat: string) => `/${splat}.md`

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
  const shapeError = checkShape(fm as Record<string, unknown>)
  if (shapeError) return `Invalid frontmatter: ${shapeError}`
  const lines = new Set(parsed.body.split('\n').map((l) => l.trim()))
  const missing = TEMPLATES[type].filter((h) => !lines.has(`## ${h}`))
  return missing.length ? `Missing template headings: ${missing.join(', ')}` : null
}

// Empty YAML values (`key:`) parse to null and count as absent
const isText = (v: unknown) => v == null || typeof v === 'string'
const isScalarObject = (v: unknown) =>
  typeof v === 'object' &&
  v !== null &&
  !Array.isArray(v) &&
  Object.values(v).every((x) => typeof x !== 'object' || x === null)
const isListOf = (v: unknown, ok: (x: unknown) => boolean) =>
  v == null || (Array.isArray(v) && v.every(ok))

// Fields the UI renders as text or lists; a wrong shape would crash the sidebar or PageView
function checkShape(fm: Record<string, unknown>): string | null {
  for (const key of ['title', 'description', 'author', 'status', 'book', 'universe']) {
    if (!isText(fm[key])) return `${key} must be text (quote numbers, e.g. "1984")`
  }
  // resource goes through the URL sanitiser, which needs a string
  const isSource = (x: unknown) =>
    isScalarObject(x) && isText((x as Record<string, unknown>).resource)
  if (!isListOf(fm.sources, isSource)) return 'sources must be a list of objects'
  if (!isListOf(fm.verified, isScalarObject)) return 'verified must be a list of objects'
  if (fm.generated != null && !isScalarObject(fm.generated)) {
    return 'generated must be an object'
  }
  return null
}

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
