// Read hooks + writes; queryFn/mutationFn swap to the real /api/wiki/... endpoints in M2
import { type QueryClient, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  acceptProposal,
  getPage,
  getProfile,
  listPages,
  listProposals,
  listVersions,
  rejectProposal,
  savePage,
  searchCandidates,
  setProfilePublic,
} from './store'
import type { PageType } from './types'

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

export const useCandidates = (query: string) =>
  useQuery({
    queryKey: ['candidates', query],
    queryFn: () => searchCandidates(query),
    enabled: query !== '',
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
    mutationFn: async (content: string) => savePage(path, content),
    onSuccess: () => refreshPage(qc, path),
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
