// Records for the fake store: what has no backend yet (Profile #112, Proposals M3, Agent candidates M3)
import type { Candidate, Profile, Proposal } from '../types'

const OZ = '/books/ostatnie-zyczenie.md'

export const proposals: Proposal[] = [
  {
    id: 1,
    page: OZ,
    prompt: 'Dodaj Nivellena do postaci',
    content:
      '## Postacie\n\n- [Nivellen](/characters/nivellen--ostatnie-zyczenie.md) — zaklęty w potwora szlachcic\n',
    base_version: 1,
    status: 'open',
    created_at: '2026-10-03T09:00:00Z',
  },
  {
    id: 2,
    page: OZ,
    prompt: 'Skróć streszczenie',
    content: '## Streszczenie\n\nKrócej.\n',
    base_version: 1,
    status: 'stale',
    created_at: '2026-10-03T10:00:00Z',
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

// The first three already have Pages (duplicate case); the rest are new books
export const candidates: Candidate[] = [
  { title: 'Ostatnie życzenie', author: 'Andrzej Sapkowski', year: 1993, cover_url: null },
  { title: 'Krew elfów', author: 'Andrzej Sapkowski', year: 1994, cover_url: null },
  { title: 'Solaris', author: 'Stanisław Lem', year: 1961, cover_url: null },
  { title: 'Miecz przeznaczenia', author: 'Andrzej Sapkowski', year: 1992, cover_url: null },
  { title: 'Lalka', author: 'Bolesław Prus', year: 1890, cover_url: null },
  { title: 'Niezwyciężony', author: 'Stanisław Lem', year: 1964, cover_url: null },
]
