// In-memory /api/wiki/pages/ on top of mockFetch, seeded from the backend fixtures
// (the same files `manage.py seed` loads)
import type { PageSummary, PageType, PageVersion, VersionKind } from '@/api/types'
import { parsePage, slugify } from '@/wiki'
import { json, mockFetch } from './mockFetch'

// copies of okf.TEMPLATES / okf.DIRS (kept literal so the mock is an independent oracle)
const TEMPLATES: Record<PageType, string[]> = {
  book: ['Streszczenie', 'Postacie', 'Miejsca', 'Wątki i motywy'],
  character: ['Opis', 'Rola w książce', 'Powiązania'],
  place: ['Opis', 'Rola w książce'],
  universe: ['Opis'],
}
const DIRS: Record<PageType, string> = {
  book: 'books',
  character: 'characters',
  place: 'places',
  universe: 'universes',
}

const files = import.meta.glob<string>('../../../backend-django/wiki/fixtures/**/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
})

// '/books/solaris.md' → raw .md
export const FIXTURES: Record<string, string> = Object.fromEntries(
  Object.entries(files).map(([file, content]) => [`/${file.split('/fixtures/')[1]}`, content]),
)

export function summary(path: string, content: string): PageSummary {
  const fm = parsePage(content).frontmatter
  return {
    path,
    type: fm.type,
    title: fm.title ?? path,
    book: fm.book ?? null,
    universe: fm.universe ?? null,
  }
}

type Version = PageVersion
type Route = (init?: RequestInit) => Response
const PREFIX = '/api/wiki/pages/'

// `overrides` ('METHOD /api/...' → Response) win over the in-memory server
export function mockWikiApi(overrides: Record<string, Route> = {}) {
  const base = mockFetch(overrides)
  const db = new Map<string, Version[]>() // path → versions, newest first
  let lastId = 0

  const write = (
    path: string,
    content: string,
    kind: VersionKind = 'edit',
    author: Version['author'] = 'human',
  ) => {
    const version = { id: ++lastId, kind, author, content, created_at: new Date().toISOString() }
    db.set(path, [version, ...(db.get(path) ?? [])])
  }
  for (const [path, content] of Object.entries(FIXTURES)) {
    const draft = parsePage(content).frontmatter.status === 'draft'
    write(path, content, draft ? 'created' : 'generation', draft ? 'human' : 'agent')
  }

  const detail = (path: string) => {
    const [latest] = db.get(path)!
    return { ...summary(path, latest.content), content: latest.content, version: latest.id }
  }

  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, init?: RequestInit) => {
      const method = init?.method ?? 'GET'
      if (`${method} ${url}` in overrides || !url.startsWith(PREFIX)) return base(url, init)
      const rest = url.slice(PREFIX.length)
      const body = () => JSON.parse(init!.body as string) as Record<string, unknown>

      if (rest === '') {
        if (method === 'GET') {
          return json(
            200,
            [...db.keys()].sort().map((p) => summary(p, db.get(p)![0].content)),
          )
        }
        const { type, title, author, year, book, universe } = body() as {
          type: PageType
          title: string
          author?: string
          year?: number
          book?: string
          universe?: string
        }
        const slug = slugify(title)
        if (!slug) return json(400, { title: ['Title needs at least one letter or digit'] })
        const perBook = type === 'character' || type === 'place'
        if (perBook && !book) return json(400, { book: ['This field is required.'] })
        if (perBook && !db.has(book!)) return json(400, { book: [`No book page at ${book}`] })
        const suffix = perBook ? `--${book!.slice('/books/'.length, -'.md'.length)}` : ''
        const path = `/${DIRS[type]}/${slug}${suffix}.md`
        if (db.has(path)) return json(409, { detail: `Page already exists: ${path}` })
        const meta = perBook ? { book } : type === 'book' ? { author, year, universe } : {}
        const yaml = Object.entries({ title, ...meta })
          .filter(([, v]) => v !== undefined)
          .map(([k, v]) => `${k}: ${JSON.stringify(v)}`)
        const headings = TEMPLATES[type].map((h) => `## ${h}\n`).join('\n')
        const head = [`type: ${type}`, ...yaml, 'status: draft'].join('\n')
        write(path, `---\n${head}\n---\n\n${headings}`, 'created')
        return json(201, detail(path))
      }

      const m = /^(.+\.md)(\/versions\/)?$/.exec(rest)
      const path = m && `/${m[1]}`
      if (!m || !path || !db.has(path)) return json(404, { detail: 'Not found.' })
      const versions = db.get(path)!
      if (m[2]) {
        return json(200, {
          data: versions.slice(0, 20),
          page: 1,
          per_page: 20,
          total: versions.length,
        })
      }
      if (method === 'PUT') {
        const { content, base_version } = body()
        if (base_version !== versions[0].id) return json(409, { detail: 'Page changed.' })
        write(path, content as string)
      }
      return json(200, detail(path))
    }),
  )
  return { write }
}
