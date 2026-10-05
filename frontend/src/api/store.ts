// In-memory fake of the wiki API, seeded from OKF fixtures. M2 replaces it with fetch('/api/...').
import { candidates, profile, proposals, versions as recordedVersions } from './fixtures/records'
import { parsePage } from '@/wiki'
import type { Candidate, Page, PageType, PageVersion, Profile, Proposal } from './types'

const files = import.meta.glob<string>('./fixtures/**/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
})

const pages = new Map<string, Page>()
const versions: PageVersion[] = []

for (const [file, content] of Object.entries(files)) {
  const path = file.replace('./fixtures', '') // OKF: file path = concept identity
  const fm = parsePage(content).frontmatter
  pages.set(path, {
    path,
    type: fm.type,
    title: fm.title ?? path,
    book: fm.book ?? null,
    universe: fm.universe ?? null,
    content,
  })

  const recorded = recordedVersions.filter((v) => v.page === path)
  if (recorded.length === 0) {
    const draft = fm.status === 'draft'
    versions.push({
      id: versions.length + 1000,
      page: path,
      kind: draft ? 'created' : 'generation',
      author: draft ? 'human' : 'agent',
      content,
      created_at: '2026-10-01T12:00:00Z',
    })
  } else {
    // The newest recorded version always holds the current page content
    const latest = recorded.length - 1
    recorded.forEach((v, i) =>
      versions.push({ ...v, content: i === latest ? content : v.content! }),
    )
  }
}

const byNewest = <T extends { created_at: string }>(a: T, b: T) =>
  b.created_at.localeCompare(a.created_at)

export function listPages(type?: PageType): Page[] {
  return [...pages.values()]
    .filter((p) => !type || p.type === type)
    .sort((a, b) => a.title.localeCompare(b.title))
}

export function getPage(path: string): Page {
  const page = pages.get(path)
  if (!page) throw new Error(`Page not found: ${path}`)
  return page
}

export function listVersions(path: string): PageVersion[] {
  return versions.filter((v) => v.page === path).sort(byNewest)
}

export function listProposals(path: string): Proposal[] {
  return proposals.filter((p) => p.page === path).sort(byNewest)
}

export function getProfile(): Profile {
  return profile
}

export function searchCandidates(query: string): Candidate[] {
  const q = query.toLowerCase()
  return candidates.filter((c) => c.title.toLowerCase().includes(q))
}
