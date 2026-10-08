# Spec — Dodanie książki: czat, pusta Strona, Generowanie (fake) (#91)

> Data: 2026-10-08 · Issue: #91 · Milestone: M1 · Decyzje: ADR-004, ADR-005 · Bazuje na: #88 (`Candidate`, `searchCandidates`), #90 (`PageView`), #92 (`TEMPLATES`, `writePage`) · Makiety: `docs/mockups/add-book.html`, `new-page.html` · Spike: `docs/superpowers/specs/2026-10-03-spike-94-agent-okf-page.md` · Przepływy: `docs/ARCHITECTURE.md` (1, 2) · Pojęcia: `CONTEXT.md` (Kandydat, Szablon, Generowanie)

## Cel

User dodaje książkę rozmową z Agentem: wpisuje tytuł lub to, co pamięta, widzi karty Kandydatów, potwierdza jedną i ląduje na nowej Stronie z pustym Szablonem, która od razu jest w panelu bocznym. Na pustej Stronie uruchamia Generowanie, widzi stan „generuję…”, a potem wypełnioną treść. Wszystko na fake store; prawdziwy Agent, SSE i źródła Kandydatów to M3.

## Decyzje

| Temat | Decyzja | Powód |
|---|---|---|
| Gdzie czat | trasa `/add`, link „Add book” w panelu bocznym nad sekcjami | makieta `add-book.html`; trasa daje adres i prosty test |
| Historia czatu | stan komponentu, znika po wyjściu z trasy | `AgentConversation` przyjdzie z prawdziwym Agentem (M3) |
| Tura czatu | mutacja `useSuggestCandidates` (zastępuje nieużywany `useCandidates`) | każda wiadomość to osobna tura, nie cache'owalny odczyt |
| Dobór Kandydatów | słowa prośby (małe litery, bez diakrytyków, ≥3 znaki) dopasowane do tytułu lub autora; brak trafień → 3 Kandydaci spoza Wiki | każda prośba daje karty (też „Dodaj wiedźmina tom 1” z makiety), test deterministyczny |
| Odpowiedź Agenta | trafienia: „Is it one of these?”; fallback: „I'm not sure. Maybe one of these?” | UI jest po angielsku (makiety) |
| Nowe fixtures | + Miecz przeznaczenia (Sapkowski, 1992), Lalka (Prus, 1890), Niezwyciężony (Lem, 1964) | obecni 3 Kandydaci mają już Strony; zostają, żeby pokazać duplikat |
| Duplikat | karta z istniejącą Ścieżką: „Already in Wiki” + link zamiast „Yes, add”; `createBook` i tak rzuca błąd | Ścieżka = tożsamość, dwie Strony jednej książki są niechciane |
| „None of these” | chowa karty, Agent: „Try a different title or author.” | najprostsze domknięcie tury |
| Ścieżka | `/books/${slugify(title)}.md`; `slugify` w `wiki.ts`: NFD, bez znaków łączących, `ł→l`, małe litery, nie-alfanumeryczne → `-`, przycięte | spike #94: slugi liczy aplikacja, nie model; ASCII jak w fixtures |
| Pusta Strona | frontmatter `type: book`, `title`, `author`, `year`, `status: draft` + nagłówki `TEMPLATES.book` bez treści; Wersja `created` / `human` | ARCHITECTURE §1; przechodzi `validateEdit`, więc Edycja działa od razu |
| Po potwierdzeniu | nawigacja na nową Stronę; panel boczny odświeżony przez `invalidateQueries(['pages'])` | Done when 2 |
| Kto może Generować | karta „This page is empty” + „Generate with Agent” tylko dla `type: book` ze `status: draft` | fake treść jest tylko dla książek (Snaut ma `draft`, ale to Postać) |
| Treść Generowania | jeden generyczny szablon w store z podstawionym tytułem i autorem, wszystkie 4 sekcje wypełnione, 1–2 Wzmianki do nieistniejących Stron (`/characters/…--<slug>.md`) | Done when 3; badge do brakującej Strony już działa (#90) |
| Frontmatter po Generowaniu | usunięte `status`, dopisane `description` i `generated: {by: agent:fake, at: <ISO now>}`; Wersja `generation` / `agent` | spike #94: `generated` stempluje aplikacja; brak `status` = Strona wypełniona |
| Generowanie nie-draftu | `generatePage` rzuca błąd | Generowanie to tylko pierwsze wypełnienie (CONTEXT); dalej są Propozycje |
| Fake opóźnienie | `await delay(FAKE_AGENT_MS)` w `mutationFn`; 1500 ms w dev, 50 ms w testach (`import.meta.env.MODE === 'test'`) | spike #94: prawdziwe Generowanie jest async; 50 ms wystarcza, żeby test zobaczył „Generating…”, a nie spowalnia suite'u |
| Stan ładowania | przycisk `disabled` z tekstem „Generating…”; błąd → `role="alert"` | wzorzec z edytora (#92) |
| Pominięte z makiet | placeholder „Empty, filled in by Generate” pod sekcjami, okładka (szary prostokąt zamiast obrazka), „Universe: …” na pustej Stronie, rok w panelu bocznym | Kandydaci nie mają okładek ani Uniwersum; nic z tego nie jest w Done when |

## Pliki

```
frontend/src/
  wiki.ts                      + slugify
  wiki.test.ts                 + testy slugify
  api/fixtures/records.ts      + 3 Kandydaci
  api/store.ts                 searchCandidates (słowa + fallback), createBook, generatePage
  api/api.test.ts              + testy searchCandidates, createBook, generatePage
  api/hooks.ts                 useSuggestCandidates, useCreateBook, useGeneratePage (− useCandidates)
  routes/add.tsx               czat + karty Kandydatów
  routes/$.tsx                 karta Generate dla pustej Strony książki
  components/Sidebar.tsx       link „Add book”
  routeTree.gen.ts             regenerowany (commitowany)
  test/add-book.test.tsx       przepływ czat → Kandydat → Strona → Generowanie; duplikat
```

## Interfejsy

```ts
// wiki.ts
export function slugify(title: string): string            // 'Krew elfów' → 'krew-elfow'

// store.ts
export function searchCandidates(prompt: string): { matched: boolean; candidates: Candidate[] }  // matched → odpowiedź Agenta
export function createBook(c: Candidate): Page             // throws if path exists
export function generatePage(path: string): Page           // throws if not a draft book

// hooks.ts
useSuggestCandidates()   // mutation: prompt → Candidate[] (po FAKE_AGENT_MS)
useCreateBook()          // mutation: Candidate → Page; invaliduje ['pages']
useGeneratePage(path)    // mutation: () → Page (po FAKE_AGENT_MS); refreshPage
```

## Testy (Done when 4)

- `wiki.test.ts`: `slugify` — polskie znaki (`ł`, `ó`, `ż`), spacje i interpunkcja, brak `-` na brzegach.
- `api.test.ts`: `searchCandidates` — trafienie po tytule, po autorze, fallback zwraca tylko Kandydatów spoza Wiki; `createBook` — treść przechodzi `validateEdit`, Wersja `created`, duplikat rzuca; `generatePage` — brak `status`, jest `generated`, Wersja `generation`, drugi raz rzuca.
- `test/add-book.test.tsx`: „Lalka” → karta → „Yes, add” → nagłówek „Lalka”, link w panelu bocznym, „Generate with Agent” → „Generating…” → treść sekcji, karta znika. Drugi przypadek: „Solaris” → „Already in Wiki” z linkiem.
- CI zielone: `make verify` (typecheck, lint, format, Vitest, build + `routeTree.gen.ts`).
