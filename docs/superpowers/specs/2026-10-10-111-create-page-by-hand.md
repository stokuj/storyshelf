# Spec — Ręczne tworzenie Strony z Szablonu (#111)

> Data: 2026-10-10 · Issue: #111 · Milestone: M2 · Zależy od: #108 (`POST /api/wiki/pages/`), #110 (ekrany na API) · Makieta: `docs/mockups/new-page-form.html`

## Cel

Bez Agenta User może tylko edytować istniejące Strony. Formularz „New page” tworzy pustą Stronę z Szablonu dowolnego Typu. Ścieżkę i Szablon buduje backend (`services.create_page`), a frontend tylko zbiera pola i obsługuje błędy.

## Decyzje

| Temat | Decyzja | Powód |
|---|---|---|
| Gdzie | osobna trasa `/new` (`routes/_app/new.tsx`); link „New page” w sidebarze pod „Add book”, mniej wyróżniony | pasuje do `/add`; dialog odrzucony |
| Formularz | kontrolowany (`useState`), natywne `radio` / `input` / `select`, bez nowych zależności | 6 pól; brak bibliotek formularzy w projekcie |
| Pola Book | Title*, Author, Year, Universe (`select` z Uniwersów Usera, „None”) | backend przyjmuje `author`, `year`, `universe` |
| Pola Character / Place | Title*, Book* (`select` z książek Usera); brak książek → `select` wyłączony + „Add a book first” | backend wymaga `book` i sprawdza, czy istnieje |
| Pola Universe | Title* | Szablon nie ma innych pól |
| Zmiana typu | pola nienależące do nowego typu nie trafiają do żądania | backend sprawdza `book`/`universe` tylko dla właściwego typu, ale body ma być czyste |
| Puste pola opcjonalne | pomijane w body (`year` jako liczba) | DRF `CharField` odrzuca `""` |
| Podgląd Ścieżki | „Path: /books/krew-elfow.md” liczony z `slugify` z `wiki.ts`; dla Postaci/Miejsc `slug--book-slug` | User widzi, co powstanie i dlaczego 409; ~3 linie |
| Błędy 400 / 409 | `apiErrorMessage(e)` w `role="alert"` nad przyciskiem, bez nawigacji | komunikat backendu (np. „Page already exists: …”) |
| Podwójny klik | przycisk „Create page” wyłączony podczas `isPending` | jedna Strona na jedno wysłanie |
| Po sukcesie | `refreshPage` (sidebar + Strona), nawigacja do `/$` z `pageSplat(page.path)` | Strona otwiera się pusta i jest w sidebarze |
| API klienta | `createBook(c)` → `createPage(input: NewPage)`; `useCreateBook` → `useCreatePage`; `add.tsx` woła `createPage({ type: 'book', title, author, year })` | jeden endpoint, jedna funkcja |

## Warstwa API (`frontend/src/api/`)

- `types.ts`: `NewPage = { type: PageType; title: string; author?: string; year?: number; book?: string; universe?: string }`.
- `wiki.ts`: `createPage(input: NewPage)` → `POST /wiki/pages/` z `JSON.stringify(input)`. `createBook` usunięte.
- `hooks.ts`: `useCreatePage()` (jak dziś `useCreateBook`: `onSuccess` → `refreshPage(qc, page.path)`). `useCreateBook` usunięte, `add.tsx` przepięty.

## UI

- `Sidebar.tsx`: link `to="/new"` „New page” pod „Add book” (obramowany, bez wypełnienia).
- `routes/_app/new.tsx`: nagłówek „New page”, opis, `fieldset` „Type” z 4 radio (Book domyślnie), pola wg tabeli, podgląd Ścieżki, alert błędu, przycisk „Create page”. Listy do `select` z `usePages('book')` i `usePages('universe')`. Etykiety pól jako `<label>` (testy szukają po nazwie).
- `routeTree.gen.ts` regenerowany i commitowany.

## Testy (Vitest, `src/test/new-page.test.tsx`)

- `mockWikiApi.ts`: `POST /api/wiki/pages/` obsługuje wszystkie Typy: Ścieżka jak w backendzie (`/{dir}/{slug}.md`, dla Postaci/Miejsc `{slug}--{book-slug}`), frontmatter z `type`, `title`, `book`/`universe` gdy podane, `status: draft`, nagłówki Szablonu danego Typu; 409 przy zajętej Ścieżce.
- Przypadki:
  1. „New page” w sidebarze → `/new`; Book „Krew elfów” → nawigacja na `/books/krew-elfow`, pusty Szablon (`draft`), link w sidebarze.
  2. Character bez wybranej książki nie wysyła żądania; z książką wysyła body z `book` i otwiera `/characters/<slug>--<book-slug>`.
  3. Puste Author/Year nie trafiają do body; Year wysłany jako liczba.
  4. Duplikat (np. „Solaris”) → alert z komunikatem 409, ścieżka zostaje `/new`.
  5. `add-book.test.tsx` dalej zielony po zmianie na `createPage`.

## Done when

1. Makieta zaakceptowana i w `docs/mockups/new-page-form.html`
2. Utworzenie „Krew elfów” jako książki otwiera pusty Szablon książki pod jej Ścieżką
3. Postać wymaga książki i ma ją we frontmatterze (`book: /books/...`)
4. Duplikat Ścieżki pokazuje błąd backendu zamiast nadpisać
5. Vitest pokrywa formularz; `make verify` zielone

## Poza zakresem

Wstępny wybór książki ze Strony książki (`?book=`), Kandydaci, czat i Generowanie (M3). Backend bez zmian.
