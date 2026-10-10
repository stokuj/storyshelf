// /api/wiki/pages/ calls; a Page path is '/books/x.md' and goes into the URL as-is
import { ApiError, api } from './client'
import type { Candidate, Page, PageSummary, PageType, PageVersion, Paginated } from './types'

const PAGE_PATH = /^\/(books|characters|places|universes)\/[a-z0-9-]+\.md$/

// Same pattern as the backend; a crafted splat must not reach another /api endpoint
const url = (path: string) => {
  if (!PAGE_PATH.test(path)) throw new ApiError(404, { detail: 'Not found.' })
  return `/wiki/pages${path}`
}

export const listPages = (type?: PageType) =>
  api<PageSummary[]>(`/wiki/pages/${type ? `?type=${type}` : ''}`)

export const getPage = async (path: string) => api<Page>(url(path))

// Only the newest 20 Versions (first page)
export const listVersions = async (path: string) =>
  api<Paginated<PageVersion>>(`${url(path)}/versions/`)

export const savePage = async (path: string, content: string, baseVersion: number) =>
  api<Page>(url(path), {
    method: 'PUT',
    body: JSON.stringify({ content, base_version: baseVersion }),
  })

export const createBook = (c: Candidate) =>
  api<Page>('/wiki/pages/', {
    method: 'POST',
    body: JSON.stringify({ type: 'book', title: c.title, author: c.author, year: c.year }),
  })
