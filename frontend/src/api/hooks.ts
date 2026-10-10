// Read hooks + writes: Pages go to /api/wiki/..., the rest still uses the fake store
import { type QueryClient, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createBook, getPage, listPages, listVersions, savePage } from './wiki'
import {
  acceptProposal,
  getProfile,
  listProposals,
  rejectProposal,
  searchCandidates,
  setProfilePublic,
} from './store'
import type { Candidate, PageType } from './types'

export const usePages = (type?: PageType) =>
  useQuery({ queryKey: ['pages', type ?? 'all'], queryFn: () => listPages(type) })

export const usePage = (path: string) =>
  // No retry: a missing page is a 404 (OKF tolerates broken links), not a transient error
  useQuery({ queryKey: ['page', path], queryFn: () => getPage(path), retry: false })

export const useVersions = (path: string) =>
  useQuery({ queryKey: ['page', path, 'versions'], queryFn: () => listVersions(path) })

export const useProposals = (path: string) =>
  useQuery({ queryKey: ['page', path, 'proposals'], queryFn: () => listProposals(path) })

export const useProfile = () => useQuery({ queryKey: ['profile'], queryFn: getProfile })

// Fake Agent latency (spike #94: real calls take 7–60 s); short in tests so pending states show
const FAKE_AGENT_MS = import.meta.env.MODE === 'test' ? 50 : 1500
const agentDelay = () => new Promise((resolve) => setTimeout(resolve, FAKE_AGENT_MS))

// One chat turn; the real Agent (M3) streams over SSE
export const useFindCandidates = () =>
  useMutation({
    mutationFn: async (prompt: string) => {
      await agentDelay()
      return searchCandidates(prompt)
    },
  })

// A Page write touches the sidebar list and everything under ['page', path]
const refreshPage = (qc: QueryClient, path: string) =>
  Promise.all([
    qc.invalidateQueries({ queryKey: ['pages'] }),
    qc.invalidateQueries({ queryKey: ['page', path] }),
  ])

export function useSavePage(path: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ content, baseVersion }: { content: string; baseVersion: number }) =>
      savePage(path, content, baseVersion),
    onSuccess: () => refreshPage(qc, path),
  })
}

export function useCreateBook() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (c: Candidate) => createBook(c),
    onSuccess: (page) => refreshPage(qc, page.path),
  })
}

export function useAcceptProposal(path: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => acceptProposal(id),
    onSuccess: () => refreshPage(qc, path),
  })
}

export function useRejectProposal(path: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => rejectProposal(id),
    onSuccess: () => refreshPage(qc, path),
  })
}

export function useSetProfilePublic() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (value: boolean) => setProfilePublic(value),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['profile'] }),
  })
}
