// Database-style records (not OKF documents) for the fake store
import type { Candidate, PageVersion, Profile, Proposal } from '../types'
import ostatnieZyczenie from './books/ostatnie-zyczenie.md?raw'

const OZ = '/books/ostatnie-zyczenie.md'
const EDITED_LINE = '- Przeznaczenie — Prawo Niespodzianki wiąże Geralta z Cintrą\n'

const ozTemplate = `---
type: book
title: Ostatnie życzenie
author: Andrzej Sapkowski
status: draft
---

## Streszczenie

## Postacie

## Miejsca

## Wątki i motywy
`

// Oldest first; the newest version has no content — the store fills it from the .md file
export const versions: (Omit<PageVersion, 'content'> & { content?: string })[] = [
  {
    id: 1,
    page: OZ,
    kind: 'created',
    author: 'human',
    content: ozTemplate,
    created_at: '2026-10-01T11:58:00Z',
  },
  {
    id: 2,
    page: OZ,
    kind: 'generation',
    author: 'agent',
    content: ostatnieZyczenie.replace(EDITED_LINE, ''),
    created_at: '2026-10-01T12:00:00Z',
  },
  { id: 3, page: OZ, kind: 'edit', author: 'human', created_at: '2026-10-02T08:30:00Z' },
]

export const proposals: Proposal[] = [
  {
    id: 1,
    page: OZ,
    prompt: 'Dodaj Nivellena do postaci',
    content: ostatnieZyczenie.replace(
      '- [Nenneke]',
      '- [Nivellen](/characters/nivellen--ostatnie-zyczenie.md) — zaklęty w potwora szlachcic\n- [Nenneke]',
    ),
    base_version: 3,
    status: 'open',
    created_at: '2026-10-03T09:00:00Z',
  },
]

export const profile: Profile = {
  handle: 'stokuj',
  about: 'Czytam fantastykę, głównie polską.',
  is_public: true,
  favorites: [
    {
      path: OZ,
      title: 'Ostatnie życzenie',
      description: 'Zbiór opowiadań, w którym poznajemy wiedźmina Geralta z Rivii.',
    },
    {
      path: '/characters/geralt--ostatnie-zyczenie.md',
      title: 'Geralt z Rivii',
      description: 'Wiedźmin, łowca potworów ze szkoły Wilka.',
    },
    {
      path: '/books/solaris.md',
      title: 'Solaris',
      description: 'Powieść o kontakcie z obcym oceanem, który materializuje ludzkie wspomnienia.',
    },
  ],
}

export const candidates: Candidate[] = [
  { title: 'Ostatnie życzenie', author: 'Andrzej Sapkowski', year: 1993, cover_url: null },
  { title: 'Krew elfów', author: 'Andrzej Sapkowski', year: 1994, cover_url: null },
  { title: 'Solaris', author: 'Stanisław Lem', year: 1961, cover_url: null },
]
