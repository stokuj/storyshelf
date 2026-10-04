# Spec — layout aplikacji i panel boczny Wiki (#89)

> Data: 2026-10-04 · Issue: #89 · Milestone: M1 · Decyzje: ADR-005 · Dane: #88 (`frontend/src/api/`) · Makiety: `docs/mockups/book.html`, `docs/mockups/universe.html` · Pojęcia: `CONTEXT.md` (Ścieżka, Uniwersum)

## Cel

Rama SPA, w której siedzą wszystkie kolejne ekrany. Po lewej panel boczny ze Stronami Wiki pogrupowanymi po Typie strony. Po prawej Strona wybrana z panelu. Każda Strona ma własny URL wyprowadzony ze Ścieżki. Uniwersum wylicza swoje książki, postacie i miejsca z frontmattera.

## Decyzje

| Temat | Decyzja | Powód |
|---|---|---|
| Routing | jedna trasa splat `routes/$.tsx` | URL i Ścieżka różnią się tylko `.md`, a jeden plik obsługuje każdy Typ strony. 4 pliki per Typ byłyby w 3/4 identyczne |
| URL ↔ Ścieżka | URL `/books/x` ↔ Ścieżka `/books/x.md` | URL zgodny z issue, tożsamością pozostaje Ścieżka (OKF) |
| Strona przed #90 | tytuł (Newsreader) i Ścieżka | #90 dopisze treść pod nagłówkiem |
| Podtytuły w panelu | tylko przy postaci i miejscu: tytuł książki | bez nich dwa „Geralt z Rivii” wyglądają identycznie. Rok i draft pomijamy, bo `Page` nie ma tych pól |
| Uniwersum | książki, postacie **i miejsca** | zgodnie z makietą. Miejsca liczymy tą samą logiką co postacie |
| Przynależność do Uniwersum | książka: `universe`; postać i miejsce: `book` → książka → `universe` | postać i miejsce mają tylko pole `book` (CONTEXT: na razie per książka) |
| `/` | pusty stan w ramie: „Pick a page from the sidebar.” | zero logiki; #91 może tu wstawić „Add book” |
| Brak Strony | komunikat „Page not found.” w `<main>` | OKF dopuszcza zepsute linki; osobna strona 404 jest zbędna |
| Fonty | `@fontsource-variable/newsreader`, `@fontsource-variable/public-sans` zamiast `@fontsource-variable/geist` | ten sam wzorzec co Geist ze szkieletu; bez zapytań do Google Fonts |
| Kolory | hexy z issue przypisane do istniejących zmiennych shadcn w `:root` | komponenty shadcn dostają paletę bez zmian w ich kodzie |
| Dark mode | blok `.dark` bez zmian | poza zakresem; makiety są tylko jasne |

## Tokeny (`src/index.css`)

| Zmienna | Wartość | Rola |
|---|---|---|
| `--background`, `--card`, `--popover` | `#FCFBF8` | paper |
| `--sidebar` | `#F6F3EE` | tło panelu |
| `--foreground` (i `*-foreground` jasnych powierzchni) | `#26201B` | ink |
| `--muted-foreground` | `#6E665E` | muted |
| `--primary`, `--sidebar-primary` | `#B5502A` | accent (terracotta) |
| `--font-heading` | `'Newsreader Variable', serif` | nagłówki |
| `--font-sans` | `'Public Sans Variable', sans-serif` | UI |

Pozostałe zmienne (`--border`, `--chart-*` itd.) zostają bez zmian, dopóki nie wymaga ich makieta.

## Pliki

```
frontend/src/
  index.css                 tokeny i fonty
  wiki.ts                   czyste funkcje: pageSplat, pagePath, groupByType, universeMembers
  wiki.test.ts              testy funkcji na fixture'ach
  components/Sidebar.tsx    panel boczny
  routes/__root.tsx         grid: Sidebar + <main><Outlet/></main>
  routes/index.tsx          pusty stan
  routes/$.tsx              Strona po Ścieżce; dla universe → widok Uniwersum
  test/renderApp.tsx        helper: cała aplikacja na URL w pamięci
  test/app.test.tsx         testy renderu (zastępuje home.test.tsx)
```

## Logika (`src/wiki.ts`)

```ts
pageSplat(path: string): string          // '/books/x.md' → 'books/x' (URL '/books/x')
pagePath(splat: string): string          // 'books/x'    → '/books/x.md'
groupByType(pages: Page[]): Record<PageType, Page[]>
universeMembers(pages: Page[], universe: string): { books: Page[]; characters: Page[]; places: Page[] }
```

- `groupByType` zachowuje kolejność wejścia (`listPages` sortuje po tytule). Klucze są zawsze wszystkie 4, także dla pustych grup.
- `universeMembers`: książki z `universe === universe`; postacie i miejsca, których `book` należy do tego zbioru książek.

## Komponenty

- **`Sidebar`**: `usePages()` → `groupByType` → 4 sekcje w kolejności Books, Characters, Places, Universes, każda z nagłówkiem i licznikiem. Element to `<Link to="/$" params={{ _splat }}>` z `activeProps` (tło i kolor accent). Przy postaci i miejscu pod tytułem drugi wiersz (muted) z tytułem książki, wyszukanym w tej samej liście po `page.book`.
- **`routes/$.tsx`**: `usePage(pagePath(_splat))`. Ładowanie → nic. Błąd → „Page not found.”. `type === 'universe'` → widok Uniwersum. Pozostałe Typy → `<h1>` z tytułem i Ścieżka w muted.
- **Widok Uniwersum** (w tym samym pliku): nagłówek jak wyżej i 3 sekcje „Books / Characters / Places in this universe” z listami linków. Dane: `usePages()` + `universeMembers`. Pusta sekcja jest ukrywana.

Etykiety UI są po angielsku, tak jak w makietach.

## Testy

1. `wiki.test.ts` na danych z `listPages()`:
   - `groupByType`: book 3, character 7, place 3, universe 1
   - `universeMembers('/universes/wiedzmin.md')`: 2 książki, 5 postaci, 2 miejsca; żadna Strona z Solaris
   - `pagePath(pageSplat(p)) === p` dla każdej Strony z fixture'ów
2. `app.test.tsx`: render routera w pamięci (`createMemoryHistory`), klik w „Krew elfów” → `location.pathname === '/books/krew-elfow'`, a link ma `aria-current="page"`.
3. `app.test.tsx`: `/` pokazuje panel i tekst pustego stanu.

## Poza zakresem

- Renderowanie treści Stron (#90)
- Wejście „Add book” (#91)
- Dark mode, responsywny lub zwijany panel, rok i draft w podtytułach: dodamy, kiedy wymaga tego makieta

## Done when

1. Panel pokazuje wszystkie Strony z fixture'ów, pogrupowane po Typie strony.
2. Klik zmienia URL na Ścieżkę Strony (bez `.md`) i podświetla element.
3. `/universes/wiedzmin` pokazuje 2 książki, 5 postaci i 2 miejsca Wiedźmina.
4. Vitest pokrywa grupowanie, widok Uniwersum i nawigację; `make verify` i CI są zielone.
