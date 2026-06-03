# M5 — Custom Shelves (design)

> Stan: 2026-06-02. Spec dla milestone M5 z ROADMAP („Następne" → Custom shelves).

## Cel

User tworzy własne nazwane kolekcje książek (np. „fantasy", po autorze, po uniwersum, własne tagi),
niezależne od statusu czytania. Półka może być publiczna lub prywatna; publiczne półki są widoczne
na profilu innego usera pod `/u/{handle}/shelves/{slug}`.

## Zakres i decyzje

| Decyzja | Wybór |
|---------|-------|
| Model pojęciowy | Custom shelf = niezależna kolekcja. **Nie** rusza statusu czytania (`ShelfEntry` z M3 zostaje bez zmian). |
| Widoczność | Profil bramkuje półki: `profile_public=False` ⇒ wszystkie półki 404. Półka prywatna 404 dla obcych, widoczna tylko właścicielowi (przez endpoint ownera). |
| Zakres | Full-stack: backend CRUD + publiczny widok + frontend + E2E (jak M3/M4). |
| UI zarządzania | Zakładka „Moje półki" na istniejącym `/shelf`. |
| Kolejność książek w półce | Wg daty dodania (`-added_at`). Bez ręcznego reorderu (YAGNI). |
| Umiejscowienie modeli | Rozszerzyć app `shelf/` (obok `ShelfEntry`), zgodnie z nazwami z ROADMAP. |

> Uwaga nazewnicza: w app `shelf/` współistnieją `ShelfEntry` (status czytania, M3) i `Shelf`/`ShelfMembership`
> (kolekcje, M5). To dwa różne byty — `ShelfEntry` **nie** jest pozycją `Shelf`. Dodać komentarz w modelu.

## Model danych (`shelf/models.py`, obok `ShelfEntry`)

### `Shelf`

| Pole | Typ | Uwagi |
|------|-----|-------|
| `owner` | FK User, `on_delete=CASCADE`, `related_name="shelves"` | właściciel |
| `name` | `CharField(max_length=100)` | nazwa wyświetlana |
| `description` | `TextField(blank=True, default="")` | opis |
| `is_public` | `BooleanField(default=False)` | widoczność (bramkowana przez `profile_public`) |
| `slug` | `SlugField` | generowany z `name`, **unikat per owner** |
| `created_at` | `DateTimeField(auto_now_add=True)` | — |
| `updated_at` | `DateTimeField(auto_now=True)` | — |

Constraints:
- `UniqueConstraint(fields=["owner", "slug"], name="unique_owner_shelf_slug")`
- `UniqueConstraint(fields=["owner", "name"], name="unique_owner_shelf_name")` — bez duplikatów nazw u jednego usera.

Slug generowany funkcją scope'owaną do ownera (osobna od globalnej `_generate_unique_slug` z `books`,
bo tam unikat jest globalny). Dwóch różnych userów może mieć półkę o tym samym slug.

### `ShelfMembership`

| Pole | Typ | Uwagi |
|------|-----|-------|
| `shelf` | FK Shelf, `on_delete=CASCADE`, `related_name="memberships"` | — |
| `book` | FK Book, `on_delete=CASCADE`, `related_name="shelf_memberships"` | — |
| `added_at` | `DateTimeField(auto_now_add=True)` | — |

Constraints:
- `UniqueConstraint(fields=["shelf", "book"], name="unique_shelf_book")`
- `Meta.ordering = ("-added_at",)`

## API

### Owner (IsAuthenticated, queryset scope'owany do `request.user`)

| Metoda | Endpoint | Akcja |
|--------|----------|-------|
| GET | `/api/shelves/` | lista moich półek |
| POST | `/api/shelves/` | utwórz (`name`, `description`, `is_public`) |
| GET | `/api/shelves/{slug}/` | szczegóły mojej półki (z książkami) |
| PATCH | `/api/shelves/{slug}/` | edycja (`name` / `description` / `is_public`) |
| DELETE | `/api/shelves/{slug}/` | usuń (cascade membershipy) |
| POST | `/api/shelves/{slug}/books/` | dodaj książkę `{book_slug}` — **idempotentne** (gdy już jest: 200, bez błędu) |
| DELETE | `/api/shelves/{slug}/books/{book_slug}/` | usuń membership — **idempotentne** (204 nawet gdy nie było) |

> Identyfikacja książki przez `book_slug` (SlugRelatedField) — spójne z `reviews/` i `shelf/` (ShelfEntry).

ViewSet w stylu `reviews/` (`get_queryset` filtruje po właścicielu, `get_permissions`).

### Publiczne (AllowAny)

| Metoda | Endpoint | Reguła |
|--------|----------|--------|
| GET | `/api/u/{handle}/shelves/` | tylko `is_public=True`; **404** gdy profil prywatny |
| GET | `/api/u/{handle}/shelves/{slug}/` | **404** gdy profil prywatny LUB półka `is_public=False` |

Endpoint publiczny nigdy nie zwraca prywatnych półek (również właścicielowi — właściciel zarządza nimi
przez `/api/shelves/`). Routing publicznych endpointów pod `/api/u/<handle>/shelves/` (jak istniejący
publiczny profil `/u/{handle}`).

## Widoczność / uprawnienia

- **Owner CRUD:** `IsAuthenticated`, `queryset = Shelf.objects.filter(owner=request.user)` → cudza półka = 404.
- **Publiczne:** rozwiąż usera po `handle`; `profile_public=False` ⇒ 404; następnie filtr `is_public=True`;
  detail 404 gdy półka nie jest publiczna. Spójne z obecnym `/u/{handle}`.

## Frontend

| Trasa | Zmiana |
|-------|--------|
| `/shelf` | zakładki: **Status czytania** (obecne) \| **Moje półki** (lista półek; utwórz: name / opis / public) |
| `/shelf/[slug]` | widok własnej półki: edycja (name/opis/public toggle), lista + usuwanie książek |
| `/books/[slug]` | kontrolka „Dodaj do półki" — dropdown moich półek z toggle membership |
| `/u/[handle]` | sekcja: lista publicznych półek usera (linki) |
| `/u/[handle]/shelves/[slug]` | publiczny widok półki: nazwa, opis, siatka książek |

## Eksport danych

Dorzucić półki + membershipy do istniejącego eksportu danych z M4
(`users/views.py` data export ZIP).

## Testy

### Backend (`DJANGO_ENV=dev`)

- Constraints: unikat `owner+slug`, `owner+name`, `shelf+book`; generowanie slug per-owner (dwóch userów ten sam slug OK).
- CRUD perms: nie da się edytować/usunąć cudzej półki (404); lista zwraca tylko własne.
- Publiczne: 404 gdy profil prywatny; 404 gdy półka prywatna; 200 + tylko publiczne na liście.
- Membership: add idempotentny (powtórny add nie dubluje), remove idempotentny (204 gdy nie było).
- Kontrakt OpenAPI: `make regenerate-openapi` + `config/tests/test_openapi_schema.py`.

### E2E (Playwright, 3–4 scenariusze)

1. Utwórz półkę + dodaj książkę z `/books/[slug]` → widoczna w „Moje półki".
2. Ustaw półkę publiczną → gość widzi ją przez `/u/[handle]/shelves/[slug]`.
3. Prywatna półka → ukryta dla gościa (404 / brak na liście).
4. Usuń półkę → znika z listy.

## Poza zakresem (YAGNI)

- Ręczny reorder książek (drag&drop, pole `position`).
- Półki systemowe / unifikacja ze statusem czytania (`ShelfEntry` zostaje osobno).
- Współdzielenie/kolaboracja na półkach, followowanie półek.
- Limity liczby półek / książek.
