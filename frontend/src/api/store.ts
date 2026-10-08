// In-memory fake of the wiki API, seeded from OKF fixtures. M2 replaces it with fetch('/api/...').
// Writes replace objects instead of mutating them, so React Query sees new data.
import { stringify } from 'yaml'
import {
  candidates,
  profile as seedProfile,
  proposals as seedProposals,
  versions as recordedVersions,
} from './fixtures/records'
import { addVerified, bookPath, parsePage, slugify, TEMPLATES, validateEdit } from '@/wiki'
import type {
  Candidate,
  Page,
  PageType,
  PageVersion,
  Profile,
  Proposal,
  VersionKind,
} from './types'

const files = import.meta.glob<string>('./fixtures/**/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
})

let pages: Map<string, Page>
let versions: PageVersion[]
let proposals: Proposal[]
let profile: Profile

function toPage(path: string, content: string): Page {
  const fm = parsePage(content).frontmatter
  return {
    path,
    type: fm.type,
    title: fm.title ?? path,
    book: fm.book ?? null,
    universe: fm.universe ?? null,
    content,
  }
}

// Seeds every record from the fixtures; tests reseed after each case (src/test/setup.ts)
export function resetStore() {
  pages = new Map()
  versions = []
  proposals = structuredClone(seedProposals)
  profile = structuredClone(seedProfile)

  for (const [file, content] of Object.entries(files)) {
    const path = file.replace('./fixtures', '') // OKF: file path = concept identity
    pages.set(path, toPage(path, content))

    const recorded = recordedVersions.filter((v) => v.page === path)
    if (recorded.length === 0) {
      const draft = parsePage(content).frontmatter.status === 'draft'
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
}
resetStore()

// Same timestamp (two writes in one millisecond) → higher id is newer
const byNewest = <T extends { id: number; created_at: string }>(a: T, b: T) =>
  b.created_at.localeCompare(a.created_at) || b.id - a.id

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

// Stale = still open, but the Page got a newer Version than the one the Agent worked on
function withStatus(p: Proposal): Proposal {
  return p.status === 'open' && p.base_version !== listVersions(p.page)[0].id
    ? { ...p, status: 'stale' }
    : p
}

export function listProposals(path: string): Proposal[] {
  return proposals
    .filter((p) => p.page === path)
    .map(withStatus)
    .sort(byNewest)
}

export function getProposal(id: number): Proposal {
  const proposal = proposals.find((p) => p.id === id)
  if (!proposal) throw new Error(`Proposal not found: ${id}`)
  return withStatus(proposal)
}

// Validates like the future API (400) and records a Version
function writePage(
  path: string,
  content: string,
  kind: VersionKind,
  author: PageVersion['author'],
): Page {
  const error = validateEdit(content, getPage(path).type)
  if (error) throw new Error(error)
  const page = toPage(path, content)
  pages.set(path, page)
  versions.push({
    id: Math.max(...versions.map((v) => v.id)) + 1,
    page: path,
    kind,
    author,
    content,
    created_at: new Date().toISOString(),
  })
  return page
}

export function savePage(path: string, content: string): Page {
  return writePage(path, content, 'edit', 'human')
}

function openProposal(id: number): Proposal {
  const proposal = getProposal(id)
  if (proposal.status !== 'open') throw new Error(`Proposal is ${proposal.status}`)
  return proposal
}

function setStatus(id: number, status: Proposal['status']) {
  proposals = proposals.map((p) => (p.id === id ? { ...p, status } : p))
}

export function acceptProposal(id: number): Page {
  const proposal = openProposal(id)
  const content = addVerified(proposal.content, `human:${profile.handle}`, new Date().toISOString())
  const page = writePage(proposal.page, content, 'proposal', 'agent')
  setStatus(id, 'accepted')
  return page
}

export function rejectProposal(id: number): void {
  openProposal(id)
  setStatus(id, 'rejected')
}

export function getProfile(): Profile {
  return profile
}

export function setProfilePublic(value: boolean): Profile {
  profile = { ...profile, is_public: value }
  return profile
}

// Fake Agent: prompt words (≥3 letters) equal to a title or author word; none → books not yet
// in the Wiki, or any books once all are added (a reply always has cards)
export function searchCandidates(prompt: string): { matched: boolean; candidates: Candidate[] } {
  const words = slugify(prompt)
    .split('-')
    .filter((w) => w.length >= 3)
  const found = candidates.filter((c) => {
    const known = slugify(`${c.title} ${c.author}`).split('-')
    return words.some((w) => known.includes(w))
  })
  if (found.length) return { matched: true, candidates: found }
  const fresh = candidates.filter((c) => !pages.has(bookPath(c.title)))
  return { matched: false, candidates: (fresh.length ? fresh : candidates).slice(0, 3) }
}

// Kandydat confirmed → Page with an empty Szablon (ARCHITECTURE flow 1)
export function createBook(c: Candidate): Page {
  const path = bookPath(c.title)
  if (pages.has(path)) throw new Error(`Page already exists: ${path}`)
  const meta = { type: 'book', title: c.title, author: c.author, year: c.year, status: 'draft' }
  const body = TEMPLATES.book.map((h) => `## ${h}\n`).join('\n')
  const content = `---\n${stringify(meta)}---\n\n${body}`
  pages.set(path, toPage(path, content))
  return writePage(path, content, 'created', 'human')
}

// Generowanie (fake): fills an empty book once; the app, not the model, stamps `generated` (spike #94)
export function generatePage(path: string): Page {
  const page = getPage(path)
  const fm = parsePage(page.content).frontmatter
  if (page.type !== 'book' || fm.status !== 'draft') {
    throw new Error('Only an empty book page can be generated')
  }
  const slug = path.slice('/books/'.length, -'.md'.length)
  const meta = {
    ...fm,
    description: 'Strona wygenerowana przez fake Agenta.',
    generated: { by: 'agent:fake', at: new Date().toISOString() },
  }
  delete meta.status
  const body = [
    `## Streszczenie\n\n„${page.title}” (${fm.author}) — streszczenie wygenerowane przez Agenta (fake, M1).`,
    `## Postacie\n\n- [Bohater](/characters/bohater--${slug}.md) — główna postać`,
    `## Miejsca\n\n- [Miasto](/places/miasto--${slug}.md) — miejsce akcji`,
    '## Wątki i motywy\n\n- Motyw przewodni — do opisania',
  ].join('\n\n')
  return writePage(path, `---\n${stringify(meta)}---\n\n${body}\n`, 'generation', 'agent')
}
