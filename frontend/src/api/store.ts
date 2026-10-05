// In-memory fake of the wiki API, seeded from OKF fixtures. M2 replaces it with fetch('/api/...').
// Writes replace objects instead of mutating them, so React Query sees new data.
import {
  candidates,
  profile as seedProfile,
  proposals as seedProposals,
  versions as recordedVersions,
} from './fixtures/records'
import { addVerified, parsePage, validateEdit } from '@/wiki'
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

export function searchCandidates(query: string): Candidate[] {
  const q = query.toLowerCase()
  return candidates.filter((c) => c.title.toLowerCase().includes(q))
}
