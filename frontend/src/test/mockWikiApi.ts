// In-memory /api/wiki/pages/ on top of mockFetch, seeded from the backend fixtures
// (the same files `manage.py seed` loads)
import type { PageSummary, PageVersion, VersionKind } from '@/api/types'
import { bookPath, parsePage } from '@/wiki'
import { json, mockFetch } from './mockFetch'

// copy of okf.TEMPLATES['book']
const BOOK_HEADINGS = ['Streszczenie', 'Postacie', 'Miejsca', 'Wątki i motywy']

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

type Version = Omit<PageVersion, 'page'>
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
        const title = body().title as string
        const path = bookPath(title)
        if (db.has(path)) return json(409, { detail: `Page already exists: ${path}` })
        const head = `---\ntype: book\ntitle: ${JSON.stringify(title)}\nstatus: draft\n---\n\n`
        write(path, head + BOOK_HEADINGS.map((h) => `## ${h}\n`).join('\n'), 'created')
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
