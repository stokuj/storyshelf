// Domain types mirroring the planned /api/wiki/... responses (docs/ARCHITECTURE.md)

export type PageType = 'book' | 'character' | 'place' | 'universe'

// GET /api/wiki/pages/ item (no content)
export interface PageSummary {
  path: string
  type: PageType
  title: string
  book: string | null
  universe: string | null
}

// DRF page-number pagination (config/pagination.py)
export interface Paginated<T> {
  data: T[]
  page: number
  per_page: number
  total: number
}

export interface Page {
  path: string // '/books/ostatnie-zyczenie.md' — identity
  type: PageType
  title: string
  book: string | null // character/place → book path
  universe: string | null // book → universe path
  content: string // raw .md: frontmatter + body (source of truth)
}

export type VersionKind = 'created' | 'generation' | 'proposal' | 'edit'

export interface PageVersion {
  id: number
  page: string // page path
  kind: VersionKind
  author: 'human' | 'agent'
  content: string
  created_at: string // ISO 8601
}

export interface Proposal {
  id: number
  page: string
  prompt: string
  content: string // proposed full .md
  base_version: number // PageVersion.id
  status: 'open' | 'accepted' | 'rejected' | 'stale'
  created_at: string
}

export interface Profile {
  handle: string
  about: string
  is_public: boolean
  favorites: { path: string; title: string; description: string }[]
}

export interface Candidate {
  title: string
  author: string
  year: number
  cover_url: string | null
}
