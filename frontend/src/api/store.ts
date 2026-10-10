// In-memory fake for what has no backend yet: Agent candidates (M3), Profile (#112), Proposals (M3).
// Writes replace objects instead of mutating them, so React Query sees new data.
import { candidates, profile as seedProfile, proposals as seedProposals } from './fixtures/records'
import { slugify } from '@/wiki'
import type { Candidate, Profile, Proposal } from './types'

let proposals: Proposal[]
let profile: Profile

// Tests reseed after each case (src/test/setup.ts)
export function resetStore() {
  proposals = structuredClone(seedProposals)
  profile = structuredClone(seedProfile)
}
resetStore()

export function listProposals(path: string): Proposal[] {
  return proposals
    .filter((p) => p.page === path)
    .sort((a, b) => b.created_at.localeCompare(a.created_at) || b.id - a.id)
}

export function getProposal(id: number): Proposal {
  const proposal = proposals.find((p) => p.id === id)
  if (!proposal) throw new Error(`Proposal not found: ${id}`)
  return proposal
}

function openProposal(id: number): Proposal {
  const proposal = getProposal(id)
  if (proposal.status !== 'open') throw new Error(`Proposal is ${proposal.status}`)
  return proposal
}

function setStatus(id: number, status: Proposal['status']) {
  proposals = proposals.map((p) => (p.id === id ? { ...p, status } : p))
}

// Only the status changes; writing the new Version comes with the Agent API (M3)
export function acceptProposal(id: number): Proposal {
  openProposal(id)
  setStatus(id, 'accepted')
  return getProposal(id)
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

// Fake Agent: prompt words (≥3 letters) equal to a title or author word; none → the first three
export function searchCandidates(prompt: string): { matched: boolean; candidates: Candidate[] } {
  const words = slugify(prompt)
    .split('-')
    .filter((w) => w.length >= 3)
  const found = candidates.filter((c) => {
    const known = slugify(`${c.title} ${c.author}`).split('-')
    return words.some((w) => known.includes(w))
  })
  if (found.length) return { matched: true, candidates: found }
  return { matched: false, candidates: candidates.slice(0, 3) }
}
