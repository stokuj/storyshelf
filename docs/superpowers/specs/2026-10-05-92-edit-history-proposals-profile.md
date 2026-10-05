# Spec — Edycja, Historia, Propozycje i Profil (#92)

> Data: 2026-10-05 · Issue: #92 (wchłonął #93) · Milestone: M1 · Decyzje: ADR-004, ADR-005 · Bazuje na: #90 (`PageView`, `parsePage`, `routes/$.tsx`) · Makiety: `docs/mockups/history.html`, `proposal.html`, `profile.html` · Przepływy: `docs/ARCHITECTURE.md` (3, 4) · Pojęcia: `CONTEXT.md` (Edycja, Wersja, Propozycja, Profil, Ulubione)

## Cel

User poprawia Stronę ręcznie i widzi każdą zmianę w Historii. Propozycje Agenta przegląda jako diff, a potem akceptuje albo odrzuca. Propozycja oparta na starej Wersji nigdy nie nadpisze nowszej Edycji. Ma też ekran Profilu z kartami Ulubionych. Wszystko działa na fake store; M2 podmienia go na `/api/...`.

## Decyzje

| Temat | Decyzja | Powód |
|---|---|---|
| Wymagane nagłówki | stała `TEMPLATES: Record<PageType, string[]>` w `wiki.ts` | Szablony nie są nigdzie zdefiniowane we frontendzie; jedna tablica wystarczy do walidacji i do przyszłego tworzenia Stron |
| Co blokuje zapis | zepsuty/brakujący frontmatter, zmiana `type`, brak nagłówka Szablonu | `type` wyznacza katalog Ścieżki (`/books/` …), więc jego zmiana zepsułaby tożsamość Strony |
| Gdzie walidacja | `validateEdit` w `wiki.ts`, wołana przez store, który rzuca błąd | store udaje API: w M2 ten sam błąd przyjdzie jako 400, a UI już go pokazuje |
| Adresy widoków | search params na trasie `$`: `?view=edit`, `?view=history[&v=<id>]`, `?view=proposal&p=<id>` | trasa `$` łapie każdą Ścieżkę; segmenty `/history` trzeba by ręcznie odcinać od splatu |
| Numer Wersji | `vN` z kolejności (najstarsza = v1), w URL `id` | id z fixture'ów nie są ciągłe (1, 2, 3, 1000+) |
| Opis Wersji z makiety | pomijamy | `PageVersion` nie ma takiego pola; rodzaj + autor + czas wystarczą |
| Status `stale` | wyliczany przy odczycie: `open` i `base_version` ≠ id najnowszej Wersji | jedna prawda (lista Wersji), nic do synchronizowania po Edycji |
| Diff | paczka `diff` (jsdiff), `diffLines` na całym `.md` | sprawdzone, przypadki brzegowe obsłużone; Agent w M3 też potrzebuje diffu |
| Zdarzenie `verified` | `yaml.parseDocument` + `addIn`, potem `String(doc)` | dopisuje do frontmattera bez przepisywania reszty formatowania; `yaml` już jest |
| Id usera w `verified` | `human:${profile.handle}` | fake nie ma sesji; handle z Profilu to jedyny id usera |
| Regenerate | przycisk `disabled` z dopiskiem „Agent arrives in M3” | prawdziwy Agent to M3 |
| Pominięte z makiet | „Refine proposal”, „Sources for this change”, podział diffu na sekcje | nie ma ich w modelu danych |
| Karty Ulubionych | tytuł + `description`, podział na książki i Postacie po prefiksie Ścieżki | CONTEXT: karta = tytuł i opis; makieta pokazuje pod Postacią tytuł książki, ale słownik wygrywa |
| Link do Profilu | `@handle` na dole panelu bocznego → `/profile` | panel nie ma jeszcze bloku usera |
| Mutacje w store | obiekty podmieniane (nowa referencja), nie modyfikowane w miejscu | React Query porównuje dane strukturalnie; ta sama zmutowana referencja nie wywoła re-renderu |
| Stan store w testach | testy mutujące w osobnych plikach | store trzyma stan w module, a Vitest izoluje moduły per plik |

## Pliki

```
frontend/
  package.json                       + diff
  src/wiki.ts                        parsePage (CRLF, pusty frontmatter), TEMPLATES, validateEdit, addVerified
  src/wiki.test.ts                   + testy parsePage, validateEdit, addVerified
  src/api/store.ts                   savePage, acceptProposal, rejectProposal, setProfilePublic; stale w listProposals
  src/api/hooks.ts                   useSavePage, useAcceptProposal, useRejectProposal, useSetProfilePublic
  src/routes/$.tsx                   validateSearch, pasek akcji, przełączanie widoków
  src/routes/profile.tsx             ekran Profilu
  src/components/PageEditor.tsx      textarea + Save/Cancel + błąd
  src/components/PageHistory.tsx     lista Wersji + podgląd Wersji
  src/components/ProposalView.tsx    prompt, diff, Accept/Reject, stale
  src/components/Sidebar.tsx         + link @handle → /profile
  src/routeTree.gen.ts               regenerowany (trasa /profile)
  src/test/edit.test.tsx             Edycja + Historia
  src/test/proposal.test.tsx         accept, reject, stale
  src/test/profile.test.tsx          Profil
```

## Logika (`src/wiki.ts`)

```ts
parsePage(content: string): { frontmatter: Frontmatter; body: string }
```

- Akceptuje `\r\n` tak samo jak `\n`.
- Pusty frontmatter (`---\n---`) daje `frontmatter = {}` (pole `type` jest wtedy `undefined`) zamiast wyjątku.
- Brak bloku `---` nadal rzuca `Error('Missing frontmatter')`. Zepsuty YAML rzuca błąd z `yaml`.

```ts
const TEMPLATES: Record<PageType, string[]> = {
  book: ['Streszczenie', 'Postacie', 'Miejsca', 'Wątki i motywy'],
  character: ['Opis', 'Rola w książce', 'Powiązania'],
  place: ['Opis', 'Rola w książce'],
  universe: ['Opis'],
}

validateEdit(content: string, type: PageType): string | null
```

Zwraca pierwszy błąd albo `null`:

1. `parsePage` rzuca albo frontmatter nie jest obiektem → `Invalid frontmatter: <komunikat>`
2. `frontmatter.type !== type` → `Page type can't change`
3. brakuje nagłówków `## <nazwa>` z `TEMPLATES[type]` (dokładne dopasowanie linii po `trim`) → `Missing template headings: Postacie, Miejsca`. Kolejność i dodatkowe nagłówki są dozwolone.

```ts
addVerified(content: string, by: string, at: string): string
```

Dopisuje `{ by, at }` na końcu listy `verified` we frontmatterze (tworzy listę, gdy jej nie ma). Treść pod frontmatterem zostaje bez zmian.

## Store i hooki (`src/api/`)

| Funkcja | Działanie |
|---|---|
| `savePage(path, content)` | `validateEdit` z obecnym `type`; błąd → `throw new Error(msg)`. Nowy obiekt `Page` z odświeżonymi `title`/`book`/`universe` i nowym `content`; dopisuje Wersję `{ kind: 'edit', author: 'human', created_at: now }`. Zwraca `Page` |
| `listProposals(path)` | jak dziś, ale Propozycja `open` z `base_version` ≠ id najnowszej Wersji Strony wraca ze `status: 'stale'` |
| `getProposal(id)` | jedna Propozycja z wyliczonym statusem; brak → `throw` |
| `acceptProposal(id)` | status ≠ `open` (także `stale`) → `throw`. Treść = `addVerified(proposal.content, 'human:' + handle, now)`, potem `validateEdit`. Zapis Strony jak w `savePage`, ale Wersja `{ kind: 'proposal', author: 'agent' }`; Propozycja → `accepted` |
| `rejectProposal(id)` | status ≠ `open` → `throw`; Propozycja → `rejected`. Strona i Wersje bez zmian |
| `setProfilePublic(value)` | nowy obiekt Profilu z `is_public = value` |

Id nowej Wersji = największe id + 1. `getProfile` i listy zwracają nowe referencje po każdej mutacji.

Hooki to `useMutation`. Po sukcesie robią `invalidateQueries`:

- `useSavePage(path)`, `useAcceptProposal(path)`, `useRejectProposal(path)`: `['pages']` i `['page', path]` (prefiks obejmuje Wersje i Propozycje).
- `useSetProfilePublic()`: `['profile']`.

Nowy hook do odczytu: `useProposal(id)`.

## Widoki

**`routes/$.tsx`**: `validateSearch` → `{ view?: 'edit' | 'history' | 'proposal'; v?: number; p?: number }` (nieznane wartości są ignorowane). Bez `view` widok Strony jak dziś, a nad nim:

- pasek akcji: linki **Edit** i **History**;
- dla każdej Propozycji `open` lub `stale`: notka „Proposal: <prompt>” z linkiem **Review** → `?view=proposal&p=<id>`.

| `view` | Komponent |
|---|---|
| `edit` | `PageEditor` |
| `history` bez `v` | `PageHistory` (lista) |
| `history` z `v` | `PageView` z treścią tej Wersji + baner |
| `proposal` | `ProposalView` |

**`PageEditor({ page })`**: link „← <tytuł>”, `<textarea aria-label="Page source">` (mono, pełna szerokość, ok. 30 wierszy) z `page.content`, przyciski **Save** i **Cancel**. Save woła `useSavePage`; błąd mutacji → `<p role="alert">` z komunikatem, treść w textarea zostaje. Sukces lub Cancel → widok Strony.

**`PageHistory({ page, version })`**:

- Lista (bez `version`): nagłówek „History”, wiersze od najnowszej: `vN`, pill rodzaju (Created / Generation / Proposal / Edit), autor (`human` / `agent`), data (`toLocaleString('en-GB')`), link **View** → `?view=history&v=<id>`. Pod listą: „Rejected proposals don't create versions.”
- Podgląd (`version` podane): baner „Viewing vN · <rodzaj> · <data>” z linkiem „Back to current” i „History”, pod nim `PageView` z `{ ...page, content: version.content, title: frontmatter.title ?? page.title }`. Brak Edit. Nieznane `v` → „Version not found.”

**`ProposalView({ page, proposalId })`**: link „← <tytuł>”, nagłówek „Proposal from the Agent”, blok „You asked” z `prompt`. Diff: `diffLines(base.content, proposal.content)`, gdzie `base` to Wersja `base_version`. Każda linia w `<pre>`: dodana na zielono z `+`, usunięta na czerwono z `−`, reszta bez znaku. Przyciski zależnie od statusu:

| Status | UI |
|---|---|
| `open` | **Accept → new version vN+1**, **Reject**; po sukcesie powrót do widoku Strony |
| `stale` | Accept `disabled`, notka „This page changed since the proposal was made.”, **Regenerate** `disabled` z „Agent arrives in M3” |
| `accepted` / `rejected` | tylko pill statusu, bez przycisków |

**`routes/profile.tsx`**: avatar z inicjałami handle, `@handle`, przełącznik `<input type="checkbox" role="switch">` „Public profile” (woła `useSetProfilePublic`), sekcja „About me”, potem „Favourite books” i „Favourite characters” jako karty (tytuł + opis, bez linku). Pusta grupa się nie renderuje. Pod spodem: „Visitors see these as cards only. Your wiki pages stay private.”

## Testy

1. `wiki.test.ts`:
   - `parsePage`: treść z `\r\n` parsuje się jak z `\n`; `---\n---\n` daje `{}`;
   - `validateEdit`: poprawna treść → `null`; zepsuty YAML → `Invalid frontmatter…`; zmiana `type` → `Page type can't change`; usunięte `## Postacie` → `Missing template headings: Postacie`;
   - `addVerified`: dopisuje zdarzenie do istniejącej listy i tworzy listę, gdy jej nie ma; body bez zmian.
2. `test/edit.test.tsx`:
   - Edit → zmiana treści → Save: Strona pokazuje nową treść, a pierwszy wiersz History to „Edit”;
   - usunięcie `## Postacie` → Save: `role="alert"` z komunikatem, Historia bez zmian;
   - History → View na v1 „Ostatniego życzenia”: widać pusty Szablon (`## Streszczenie`, bez treści streszczenia), brak linku Edit w widoku podglądu.
3. `test/proposal.test.tsx`:
   - Accept: pierwszy wiersz History to „Proposal”, treść Strony ma nową linię (Nivellen), a frontmatter ma drugie zdarzenie `verified`;
   - Reject: treść Strony i liczba Wersji bez zmian, notka o Propozycji znika;
   - Edycja, a potem widok Propozycji: Accept jest `disabled`, widać notkę o zmianie Strony.
4. `test/profile.test.tsx`: `@stokuj`, „About me” z treścią z fixture'a, przełącznik zaznaczony, 2 karty książek i 1 karta Postaci; klik przełącznika go odznacza.

## Poza zakresem

- Diff między Wersjami, przywracanie starej Wersji, ostrzeżenie o niezapisanych zmianach
- Walidacja po stronie serwera, API Ulubionych, cudze publiczne Profile (M2)
- Prawdziwy Agent, Regenerate, Refine proposal (M3)

## Done when

1. Zapis Edycji pokazuje nową treść i dodaje „Edit” na górze Historii.
2. Usunięcie wymaganego nagłówka Szablonu blokuje zapis i pokazuje błąd.
3. View na starszej Wersji pokazuje jej treść tylko do odczytu.
4. Accept dodaje „Proposal” w Historii, a frontmatter Strony dostaje zdarzenie `verified`.
5. Reject nie zmienia Strony ani Historii.
6. Po Edycji otwarta Propozycja jest `stale`, a Accept jest wyłączony.
7. Profil pokazuje about, przełącznik publiczności i karty Ulubionych z fixture'ów.
8. Vitest pokrywa powyższe; `make verify` i CI są zielone.
