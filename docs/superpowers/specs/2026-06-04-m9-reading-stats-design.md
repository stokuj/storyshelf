# M9 — Statystyki czytania (design / spec)

> Status: zatwierdzony 2026-06-04. Gałąź: `feat/m9-reading-stats`.
> Następny krok: `/writing-plans`.

## Cel

Statystyki czytania **per użytkownik**, prywatne (tylko własne). Agregacje w API + frontend
z prostymi wykresami. Moduł samodzielny, bez zależności od social.

Zakres z ROADMAP: książki/rok, rozkład ocen, time-on-shelf.

## Decyzje (z brainstormingu)

| # | Decyzja | Wybór |
|---|---------|-------|
| D1 | Brak dat przeczytania w danych | **Auto-set `finish_date`** przy przejściu statusu na `READ` (opcja A) |
| D2 | Widoczność | **Tylko własne, prywatne** — `GET /api/users/me/stats/`, authenticated (opcja A) |
| D3 | Wykresy | **Ręczne słupki** (CSS/flex, Tailwind) — zero nowych zależności (opcja A) |
| D4 | Umiejscowienie | Dedykowana trasa **`/stats`** (authenticated) |
| D5 | Aplikacja backendu | **Bez nowej aplikacji** — logika w `users/` |

## 1. Dane: auto-set `finish_date` (enabler)

Dziś `ShelfEntry.finish_date` / `start_date` istnieją i są zapisywalne w serializerze, ale
front nie ma kontrolki do ich ustawiania i nic ich nie wypełnia automatycznie → w praktyce
zawsze `NULL`. Bez daty przeczytania „książki/rok" i „time-on-shelf" nie mają z czego liczyć.

**Zmiana w `ShelfEntrySerializer` (create + update):** jeśli wynikowy `status == READ`,
`finish_date` nie zostało podane w żądaniu i `instance.finish_date` jest puste →
ustaw `finish_date = date.today()`.

Reguły:
- Pierwsze przejście do `READ` ustawia datę.
- Ponowne zapisy w statusie `READ` **nie nadpisują** istniejącej `finish_date` (zachowujemy
  pierwsze ukończenie).
- Zejście ze statusu `READ` **nie czyści** daty (zostaje historyczna).
- `start_date` nie jest ruszane — niepotrzebne (time-on-shelf liczony z `created_at`).

Uzasadnienie umiejscowienia: logika w serializerze, nie w modelu/sygnale — to jedyna ścieżka
zapisu z frontu, a semantyka „stało się READ" jest tam najczytelniejsza. Django admin tego nie
wyzwoli (akceptowalne — admin nie jest typową ścieżką użytkownika).

Edge (znany, drobny): oznaczenie `READ` przez pomyłkę i cofnięcie zostawia `finish_date`.
Akceptowalne w MVP.

## 2. Backend — endpoint statystyk

`GET /api/users/me/stats/`
- Authenticated; gość → `401`.
- Wpięty w `users/urls/users.py` (wzorzec `me/*`).
- **Bez nowej aplikacji:** czysta funkcja agregująca `build_user_stats(user) -> dict`
  w `users/stats.py` (testowalna bez HTTP), cienki `MyStatsView` w `users/views.py`,
  `UserStatsSerializer` dla kontraktu OpenAPI (drf-spectacular).

### Kształt odpowiedzi

```json
{
  "status_counts": { "want_to_read": 3, "reading": 1, "read": 12 },
  "totals": { "total_books": 16, "pages_read": 4200, "avg_rating_given": 3.8 },
  "books_per_year": [ { "year": 2025, "count": 7 }, { "year": 2026, "count": 5 } ],
  "rating_distribution": [
    { "rating": 1, "count": 0 },
    { "rating": 2, "count": 1 },
    { "rating": 3, "count": 3 },
    { "rating": 4, "count": 4 },
    { "rating": 5, "count": 4 }
  ],
  "time_on_shelf_days": 23.5
}
```

### Agregacje

| Pole | Źródło / metoda |
|------|-----------------|
| `status_counts` | `ShelfEntry.filter(user).values('status').annotate(Count('id'))` → mapa z zerami dla brakujących statusów |
| `totals.total_books` | liczba `ShelfEntry` użytkownika |
| `totals.pages_read` | `Sum('book__page_count')` po `ShelfEntry` ze statusem `READ` (NULL strony pomijane) |
| `totals.avg_rating_given` | `Rating.filter(user).aggregate(Avg('rating'))`; `null` gdy brak ocen, inaczej zaokrąglone do 1 miejsca |
| `books_per_year` | `ShelfEntry.filter(user, status=READ, finish_date__isnull=False)` → `ExtractYear('finish_date')`, group by, `order_by('year')` |
| `rating_distribution` | `Rating.filter(user).values('rating').annotate(Count('id'))` → zero-fill koszyki 1–5, posortowane rosnąco |
| `time_on_shelf_days` | READ z `finish_date__isnull=False`: średnia `(finish_date - created_at.date())` w dniach, liczona w Pythonie po małym `values_list`; `null` gdy brak |

Wartości `avg_rating_given` i `time_on_shelf_days` = `null` przy braku danych.
`books_per_year` i `rating_distribution` mogą być pustą listą / samymi zerami (nowy user).

## 3. Frontend

- Trasa **`/stats`**:
  - `+page.server.ts` ładuje SSR: `getMyStats(fetch, true)`.
  - `+page.svelte` renderuje sekcje; przy braku danych w sekcji → „No data yet".
- `src/lib/api/stats.ts`: `getMyStats(fetchFn, isServerSide)` (wzorzec `apiFetch`),
  typ `UserStats` (w `stats.ts` lub `lib/types`).
- Komponent `BarChart.svelte`: przyjmuje `{ label: string; value: number }[]`,
  rysuje słupki flexem z wysokościami znormalizowanymi do `max`, Tailwind, zero deps.
  Użyty 2×: książki/rok, rozkład ocen. Liczby (status counts, totals, time-on-shelf)
  w istniejącym `Card`.
- Link „Stats" w `AppShell.svelte` obok „Shelf" — ten sam auth-guard (widoczny tylko dla
  zalogowanych).

## 4. Testy

- **Backend (`build_user_stats` + endpoint):** status counts, `books_per_year` z `finish_date`,
  zero-fill rozkładu ocen, `time_on_shelf_days`, pusty user (zera / null / puste listy),
  gość → `401`.
- **Auto-set `finish_date`:** przejście `→ READ` ustawia datę; ponowny zapis `READ` nie
  nadpisuje; create bezpośrednio jako `READ` ustawia; jawnie podane `finish_date` respektowane.
- **OpenAPI:** `UserStatsSerializer` → `make regenerate-openapi`; kontrakt-test
  (`config/tests/test_openapi_schema.py`) zielony.
- **Frontend:** `npm run check` + `npm run lint`.
- **E2E (opcjonalnie):** 1 lekki scenariusz — oznacz książkę `READ` → `/stats` pokazuje
  niezerowe liczby. Pominąć, jeśli okaże się flaky.

## Zakres / granice (co NIE wchodzi)

- Brak publicznych statystyk na cudzym profilu (`/api/u/{handle}/stats/`) — osobny pomysł „Kiedyś".
- Brak kontrolki `start_date`/`finish_date` w UI półki — auto-set wystarcza.
- Brak biblioteki wykresów — ręczne słupki.
- Brak nowej aplikacji Django.
- Reading streak / yearly wrap — „Kiedyś" (po M9).

## Jednostki (izolacja)

| Jednostka | Odpowiedzialność | Zależy od |
|-----------|------------------|-----------|
| `users/stats.py::build_user_stats` | Czysta agregacja user → dict | `ShelfEntry`, `Rating`, `Book` |
| `MyStatsView` | Auth + zwrot dict | `build_user_stats`, `UserStatsSerializer` |
| `UserStatsSerializer` | Kontrakt OpenAPI | — |
| `ShelfEntrySerializer` (zmiana) | Auto-set `finish_date` na READ | `date.today` |
| `BarChart.svelte` | Render słupków z `{label,value}[]` | — |
| `/stats` route | SSR load + layout sekcji | `getMyStats`, `BarChart`, `Card` |
