# Spec — typy domenowe i fake warstwa danych (#88)

> Data: 2026-10-04 · Issue: #88 · Milestone: M1 · Decyzje: ADR-004, ADR-005 · Model: `docs/ARCHITECTURE.md` · Pojęcia: `CONTEXT.md`

## Cel

Ekrany #89–#93 budujemy na docelowym modelu danych. `frontend/src/api/` daje typy i hooki TanStack Query nad fixture'ami OKF. W M2 zmienia się tylko wnętrze `queryFn` (na `fetch('/api/wiki/...')`), a ekrany zostają bez zmian.

## Decyzje

| Temat | Decyzja | Powód |
|---|---|---|
| Kształt `Page` | surowy `content` (frontmatter + treść) oraz zdenormalizowane `path`, `type`, `title`, `book`, `universe` | tak jak w ARCHITECTURE: źródłem prawdy jest `content`, a kolumny służą do zapytań |
| Nazwy pól | `snake_case` | DRF domyślnie zwraca `snake_case`, więc w M2 nie trzeba mapować pól |
| Brak wartości | `null`, nie `?` | API zawsze zwraca pole |
| Frontmatter | paczka `yaml` w `dependencies` | parsuje cały YAML (`verified`, `sources`); w runtime buduje kolumny z fixture'ów. W M2 do usunięcia, jeśli nic poza tym jej nie używa |
| Magazyn | jedna `Map<path, Page>` w pamięci modułu, zasilana z fixture'ów | #91–#93 dopiszą mutacje do tego samego magazynu |
| Hooki | tylko odczyty | mutacje dojdą w ekranach, które ich potrzebują (#91–#93) |
| Ładowanie `.md` | `import.meta.glob('./fixtures/**/*.md', { query: '?raw', import: 'default', eager: true })` | natywne w Vite, działa też w Vitest; bez dodatkowych zależności |
| Ścieżka Strony | wyliczana z położenia pliku (`fixtures/books/x.md` → `/books/x.md`) | OKF: ścieżka pliku = tożsamość konceptu |
| Wersje, Propozycje, Profil, Kandydaci | obiekty TS w `fixtures/records.ts` | to rekordy bazy danych, nie dokumenty OKF |
| Opóźnienie, błędy sieci | brak | YAGNI; stan „generuję…” doda #91 |

## Pliki

```
frontend/src/api/
  types.ts            typy domenowe
  store.ts            ładuje fixtures, parsuje frontmatter, funkcje odczytu
  hooks.ts            hooki useQuery
  api.test.ts         testy
  fixtures/
    records.ts        Wersje, Propozycje, Profil, Kandydaci
    universes/  books/  characters/  places/   *.md
```

## Typy (`types.ts`)

```ts
export type PageType = 'book' | 'character' | 'place' | 'universe'

export interface Page {
  path: string              // '/books/ostatnie-zyczenie.md' — identity
  type: PageType
  title: string
  book: string | null       // character/place → book path
  universe: string | null   // book → universe path
  content: string           // raw .md: frontmatter + body (source of truth)
}

export type VersionKind = 'created' | 'generation' | 'proposal' | 'edit'

export interface PageVersion {
  id: number
  page: string              // page path
  kind: VersionKind
  author: 'human' | 'agent'
  content: string
  created_at: string        // ISO 8601
}

export interface Proposal {
  id: number
  page: string
  prompt: string
  content: string           // proposed full .md
  base_version: number      // PageVersion.id
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
```

`PageVersion.kind` nie występuje w ARCHITECTURE, a potrzebuje go #92 (Created / Generation / Proposal / Edit). Dopisujemy je w `docs/ARCHITECTURE.md` (model danych) w ramach tego taska.

## Magazyn (`store.ts`)

- Przy imporcie modułu: każdy plik `.md` → odcięcie bloku `---…---` → `yaml.parse` → `Page`. `title`, `book` i `universe` pochodzą z frontmattera, a brak pola zamienia się na `null`.
- Każda Strona, która nie ma wpisu w `records.ts`, dostaje jedną Wersję z bieżącym `content`: `kind: 'created'` przy `status: draft`, w pozostałych przypadkach `kind: 'generation'`, `author: 'agent'`. Dzięki temu każda Strona ma co najmniej jedną Wersję (CONTEXT).
- Najnowsza Wersja zawsze ma ten sam `content` co Strona. W `records.ts` najnowsza Wersja nie ma pola `content`; `store` wpisuje tam treść z pliku `.md`.
- Funkcje odczytu, nazwane jak docelowe endpointy:

| Funkcja | Endpoint w M2 | Zachowanie |
|---|---|---|
| `listPages(type?)` | `GET /api/wiki/pages/?type=` | sortowane po `title` |
| `getPage(path)` | `GET /api/wiki/pages/{path}` | brak Strony → `throw new Error('Page not found: …')` (odpowiednik 404) |
| `listVersions(path)` | `GET …/{path}/versions/` | od najnowszej |
| `listProposals(path)` | `GET …/{path}/proposals/` | od najnowszej |
| `getProfile()` | `GET /api/users/me/` (profil) | — |
| `searchCandidates(query)` | `/api/agent/chat/` (Kandydaci) | filtr po tytule bez rozróżniania wielkości liter |

## Hooki (`hooks.ts`)

| Hook | `queryKey` |
|---|---|
| `usePages(type?)` | `['pages', type ?? 'all']` |
| `usePage(path)` | `['page', path]` |
| `useVersions(path)` | `['page', path, 'versions']` |
| `useProposals(path)` | `['page', path, 'proposals']` |
| `useProfile()` | `['profile']` |
| `useCandidates(query)` | `['candidates', query]`, `enabled: query !== ''` |

Każdy hook to `useQuery({ queryKey, queryFn: () => <funkcja ze store> })`. W `src/api/` nie ma `any`.

## Szablony (nagłówki H2)

| Typ | Sekcje | Źródło |
|---|---|---|
| `book` | Streszczenie · Postacie · Miejsca · Wątki i motywy | spike #94 |
| `character` | Opis · Rola w książce · Powiązania | makieta `Character.dc.html` |
| `place` | Opis · Rola w książce | założenie, analogicznie do `character` |
| `universe` | Opis | założenie; listy książek i postaci wylicza #89 z pól `book`/`universe` |

Wzmianki w Stronie książki mają format ze spike'a #94: `- [Imię](/characters/<slug>--<book>.md) — rola`.

## Fixtures

Frontmatter zgodny z OKF v0.2: `type`, `title`, `description`, `author` (książka), `book` / `universe` (ścieżki), `generated: { by, at }`, opcjonalnie `status`, `sources` i `verified`.

| Świat | Strony (`.md`) |
|---|---|
| Wiedźmin | `universes/wiedzmin` · `books/ostatnie-zyczenie`, `books/krew-elfow` · `characters/geralt--ostatnie-zyczenie`, `geralt--krew-elfow`, `jaskier--ostatnie-zyczenie`, `yennefer--ostatnie-zyczenie`, `renfri--ostatnie-zyczenie` · `places/blaviken--ostatnie-zyczenie`, `kaer-morhen--krew-elfow` |
| Solaris | `books/solaris` (bez `universe`) · `characters/kris-kelvin--solaris`, `harey--solaris`, `snaut--solaris` · `places/stacja-solaris--solaris` |

Fixtures celowo pokrywają przypadki brzegowe potrzebne kolejnym ekranom:

| Przypadek | Gdzie | Dla |
|---|---|---|
| książka bez Uniwersum | `books/solaris` | #89 |
| ta sama postać w dwóch książkach | `geralt--*` | #89 („Also in this universe”) |
| Wzmianka bez własnej Strony | `[Nenneke](/characters/nenneke--ostatnie-zyczenie.md)` w `ostatnie-zyczenie` | #90 (zepsuty Odnośnik) |
| `verified` + `sources` | `books/ostatnie-zyczenie` | #90 (nagłówek) |
| pusty Szablon, `status: draft` | `characters/snaut--solaris` | #90, #91 |

`records.ts`:
- `ostatnie-zyczenie`: 3 Wersje (`created` → `generation` → `edit`) oraz 1 Propozycja `open` oparta na najnowszej Wersji (#92, #93)
- Profil `handle: 'stokuj'` z Ulubionymi: Ostatnie życzenie, Geralt (Ostatnie życzenie), Solaris
- 3 Kandydaci: Ostatnie życzenie (1993), Krew elfów (1994), Solaris (1961)

## Testy (`api.test.ts`)

1. `renderHook(() => usePage('/books/ostatnie-zyczenie.md'))` z `QueryClientProvider` zwraca Stronę, której `content` pasuje do `/\]\(\/characters\/[^)]+\.md\)/`. (Done when 2)
2. Każdy plik fixture ma `type` z listy `book | character | place | universe`, a katalog odpowiada typowi (`/books/` → `book` itd.). (Done when 3)
3. Każde niepuste pole `book` i `universe` wskazuje istniejącą Stronę. Łapie literówki w ścieżkach.

## Zmiany poza `frontend/src/api/`

- `frontend/package.json`: `yaml` w `dependencies`.
- `docs/ARCHITECTURE.md`: `PageVersion` dostaje `kind: created|generation|proposal|edit`.

## Poza zakresem

- Prawdziwe HTTP, auth i typy z OpenAPI (M2).
- Mutacje: tworzenie Strony, Edycja, Generowanie, akceptacja i odrzucenie Propozycji (#91–#93).
- UI i routing (#89+).

## Kryteria akceptacji

1. `npm run typecheck` przechodzi; w `src/api/` nie ma `any`.
2. Test 1 przechodzi (hook → Strona książki ze Wzmianką Postaci).
3. Test 2 przechodzi (poprawne `type` we wszystkich fixture'ach).
4. `npm run lint`, `format:check`, `test` i `build` przechodzą; CI zielone.
