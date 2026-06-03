# Google Books Import — Design Spec

> Status: approved design, 2026-06-03. Branch: `feat/google-books-import`.

## Cel

Admin-owe narzędzie CLI do importu książek z Google Books API po ISBN, żeby
zastąpić ręczne wpisywanie danych w Django adminie / przez API.

## Zakres i decyzje

| Wymiar | Decyzja |
|--------|---------|
| Kto / po co | Narzędzie dla admina — import do wspólnego katalogu |
| Interfejs | Management command (CLI), wzorem `seed_books.py` |
| Wejście | ISBN (pozycyjne argumenty i/lub `--file`) |
| Dedup | Po `isbn` (już `unique` w modelu); istniejąca książka → **update (pełny overwrite)** |
| `categories` Google | **split po `/`** na osobne `genres`; `tags` puste |
| Zapis | Reuse `BookWriteSerializer` (create / update przez `instance`) |
| Klient HTTP | stdlib `urllib.request` (zero nowych zależności) |
| API key | Opcjonalny (`GOOGLE_BOOKS_API_KEY`), działa bez |

Świadomie **poza zakresem**: import z OpenLibrary/Goodreads, UI we froncie,
import na prywatną półkę usera, scalanie/moderacja duplikatów, harmonogram/cron.

## Interfejs komendy

```
manage.py import_books <isbn> [<isbn> ...] [--file PATH] [--dry-run]
```

- pozycyjne ISBN-y (0+)
- `--file PATH` — plik tekstowy, jeden ISBN na linię; puste linie i linie z `#` pomijane
- `--dry-run` — pobierz + zmapuj + wypisz, **bez zapisu do DB** (bezpiecznik przy overwrite)
- co najmniej jeden ISBN (z argumentów lub pliku) wymagany, inaczej błąd użycia

## Pobranie z Google Books

- `GET https://www.googleapis.com/books/v1/volumes?q=isbn:<isbn>`
- bierzemy `items[0].volumeInfo` (pierwszy wynik)
- jeśli `totalItems == 0` lub brak `items` → „not found", pomiń
- klucz: `GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY", "")` w `config/settings/base.py`;
  jeśli ustawiony → dopisz `&key=<klucz>` do URL. Bez klucza działa (niższy limit, OK do dev).
- `urllib.request.urlopen` z timeoutem (np. 10s), parse JSON

## Mapowanie pól

Pure helper `_map_volume_info(volume_info: dict, isbn: str) -> dict` — testowalny bez DB.

| Google `volumeInfo` | `Book` (dict do serializera) | Transform |
|---|---|---|
| `title` | `title` | jak jest (subtitle ignorowany) |
| `authors[]` | `authors[]` | jak jest (lista stringów) |
| `publishedDate` | `year` | pierwsze 4 cyfry → int; brak → pomiń pole |
| `description` | `description` | strip tagów HTML |
| `pageCount` | `page_count` | int; brak/0 → pomiń pole |
| `imageLinks.thumbnail` | `cover_url` | `http://` → `https://`; brak → pomiń |
| (ISBN z inputu) | `isbn` | klucz wyszukania = kanoniczny |
| `categories[]` | `genres[]` | każdy string split po `/`, strip, dedup, odfiltruj puste |
| — | `tags` | `[]` |
| — | `serie`, `position_in_series` | nie ustawiamy (null) |
| `averageRating` / `ratingsCount` | **NIE importujemy** | nasze `avg_rating`/`ratings_count` liczy sygnał z modelu `Rating` |

Pola bez wartości po prostu nie trafiają do dict — `BookWriteSerializer` ma dla
nich defaulty/`required=False`. `title` jest wymagany — brak → „skipped".

## Dedup / zapis

Dla każdego ISBN po zmapowaniu:

1. `Book.objects.filter(isbn=isbn).first()`
2. istnieje → `BookWriteSerializer(instance, data=mapped)` → `is_valid()` → `save()` (update, pełny overwrite)
3. nie istnieje → `BookWriteSerializer(data=mapped)` → `is_valid()` → `save()` (create)
4. `--dry-run` → pomiń kroki 2–3, tylko wypisz zmapowany dict

M2M (authors/genres) i slug obsługuje serializer + model `save()` — nic nie duplikujemy.

## Błędy i podsumowanie

Per ISBN łapiemy wyjątki i lecimy dalej (jeden zły ISBN nie wywala całości):

| Sytuacja | Klasyfikacja |
|----------|--------------|
| `totalItems == 0` / brak `items` | not found |
| błąd sieci / HTTP / timeout / zły JSON | failed |
| brak `title` w wyniku | skipped |
| serializer `is_valid()` == False | failed (wypisz błędy) |
| OK, nowa | created |
| OK, istniejąca | updated |

Na końcu podsumowanie: `created: X, updated: Y, skipped: Z, not found: W, failed: V`.
Exit code ≠ 0, jeśli było ≥1 `failed`.

## Pliki

- Create: `backend-django/books/management/commands/import_books.py`
  (komenda + pure helper `_map_volume_info` + fetch)
- Modify: `backend-django/config/settings/base.py` (+`GOOGLE_BOOKS_API_KEY`)
- Test: `backend-django/books/tests/test_import_books.py`
- Modify: `docs/ROADMAP.md` (po implementacji: „Importer książek…" z „Kiedyś" → „Zrobione")

## Testy (Django TestCase, `DJANGO_ENV=dev`)

Mock `urllib.request.urlopen`, karmiony fixture JSON — **zero realnej sieci**.

- create nowej książki z pełnego wyniku
- update istniejącej (po ISBN) → pełny overwrite pól
- `"Fiction / Fantasy / Epic"` → 3 osobne genres
- wiele `categories` stringów → suma genres, dedup
- brakujące pola (`publishedDate`, `pageCount`, `imageLinks`) → książka zapisana bez nich
- `averageRating`/`ratingsCount` z Google **nie** nadpisują naszych
- `totalItems == 0` → not found, brak zapisu
- wiele ISBN w jednym wywołaniu → poprawne liczniki
- `--file` parsuje ISBN-y, pomija `#`/puste
- `--dry-run` → nic nie zapisane w DB
- (pure) `_map_volume_info` testowany bez DB na kilku kształtach `volumeInfo`
