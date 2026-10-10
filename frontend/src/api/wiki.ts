// /api/wiki/pages/ calls; a Page path is '/books/x.md' and goes into the URL as-is
import { api } from './client'
import type { Candidate, Page, PageSummary, PageType, PageVersion, Paginated } from './types'

const url = (path: string) => `/wiki/pages${path}`

export const listPages = (type?: PageType) =>
  api<PageSummary[]>(`/wiki/pages/${type ? `?type=${type}` : ''}`)

export const getPage = (path: string) => api<Page>(url(path))

// Only the newest 20 Versions (first page)
export const listVersions = (path: string) => api<Paginated<PageVersion>>(`${url(path)}/versions/`)

export const savePage = (path: string, content: string, baseVersion: number) =>
  api<Page>(url(path), {
    method: 'PUT',
    body: JSON.stringify({ content, base_version: baseVersion }),
  })

export const createBook = (c: Candidate) =>
  api<Page>('/wiki/pages/', {
    method: 'POST',
    body: JSON.stringify({ type: 'book', title: c.title, author: c.author, year: c.year }),
  })
