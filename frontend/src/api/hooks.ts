// Read hooks; queryFn swaps to the real /api/wiki/... endpoints in M2
import { useQuery } from '@tanstack/react-query'
import {
  getPage,
  getProfile,
  listPages,
  listProposals,
  listVersions,
  searchCandidates,
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
