import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { createElement, type ReactNode } from 'react'
import { usePage } from './hooks'
import {
  acceptProposal,
  getProfile,
  listProposals,
  rejectProposal,
  searchCandidates,
  setProfilePublic,
} from './store'

function wrapper({ children }: { children: ReactNode }) {
  return createElement(QueryClientProvider, { client: new QueryClient() }, children)
}

test('usePage returns a book page with a version and a character mention', async () => {
  const { result } = renderHook(() => usePage('/books/ostatnie-zyczenie.md'), { wrapper })
  await waitFor(() => expect(result.current.isSuccess).toBe(true))
  expect(result.current.data?.type).toBe('book')
  expect(typeof result.current.data?.version).toBe('number')
  expect(result.current.data?.content).toMatch(/\]\(\/characters\/[^)]+\.md\)/)
})

const OZ = '/books/ostatnie-zyczenie.md'
const status = (id: number) => listProposals(OZ).find((p) => p.id === id)?.status

test('accepting an open proposal marks it accepted', () => {
  expect(status(1)).toBe('open')
  expect(acceptProposal(1).status).toBe('accepted')
  expect(status(1)).toBe('accepted')
})

test('a rejected or stale proposal cannot be accepted', () => {
  rejectProposal(1)
  expect(status(1)).toBe('rejected')
  expect(() => acceptProposal(1)).toThrow('Proposal is rejected')
  expect(() => acceptProposal(2)).toThrow('Proposal is stale')
})

test('setProfilePublic replaces the profile object', () => {
  const before = getProfile()
  expect(setProfilePublic(false).is_public).toBe(false)
  expect(getProfile()).not.toBe(before)
})

const titles = (prompt: string) => searchCandidates(prompt).candidates.map((c) => c.title)

test('searchCandidates matches title or author words, ignoring case and diacritics', () => {
  expect(titles('lalka')).toEqual(['Lalka'])
  expect(titles('Dodaj LEM').sort()).toEqual(['Niezwyciężony', 'Solaris'])
  expect(titles('krew elfow')).toEqual(['Krew elfów'])
  expect(searchCandidates('sapkowski').matched).toBe(true)
})

test('searchCandidates falls back to the first three candidates', () => {
  const result = searchCandidates('Dodaj wiedźmina tom 1')
  expect(result.matched).toBe(false)
  expect(result.candidates.map((c) => c.title)).toEqual([
    'Ostatnie życzenie',
    'Krew elfów',
    'Solaris',
  ])
})

test('searchCandidates matches whole words only', () => {
  expect(searchCandidates('Nie pamiętam tytułu').matched).toBe(false)
  expect(searchCandidates('witcher and sorceress').matched).toBe(false)
})
