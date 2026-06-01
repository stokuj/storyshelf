# M4 — Reviews (design)

> Stan: 2026-06-01 · Branch: `phase/m4-reviews`

## Cel

Tekstowe recenzje książek. Jeden user → jedna recenzja na książkę. Recenzje
publiczne (czytelne dla wszystkich), pisane przez zalogowanych. Gwiazdka oceny
przychodzi z istniejącego modelu `Rating` (M3) — recenzja jej nie duplikuje.

## Decyzje (z brainstormingu)

| # | Pytanie | Decyzja |
|---|---------|---------|
| 1 | Review ↔ Rating | Rozłączne modele. Review = sam tekst; UI łączy z `Rating` przy odczycie. `avg_rating` bez zmian. |
| 2 | Kardynalność | Jedna recenzja per (user, book) — `UniqueConstraint`. API jak ratings: PUT-upsert + DELETE. |
| 3 | Pola | Tylko `body` (+ `created_at`/`updated_at`). Bez tytułu, bez spoiler-flag. |
| 4 | Widoczność | Publiczne dla wszystkich (też niezalogowanych). `profile_public` ignorowane dla recenzji. |
| 5 | Własna recenzja | Dedykowany endpoint `GET /api/reviews/me/?book_slug=X` → recenzja albo 404. |

## Model danych

`backend-django/reviews/models.py` — bliźniaczo do `Rating`/`ShelfEntry`:

```python
class Review(models.Model):
    user = FK(User, on_delete=CASCADE, related_name="reviews", db_index=True)
    book = FK("books.Book", on_delete=CASCADE, related_name="reviews", db_index=True)
    body = TextField()                      # min 1 / max ~5000 — walidacja w serializerze
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        constraints = [UniqueConstraint(fields=["user", "book"], name="unique_user_book_review")]
        ordering = ("-created_at",)
```

**Bez sygnału, bez przeliczania `avg_rating`** — średnia zostaje napędzana przez `Rating` (M3).

## API surface

| Metoda | Endpoint | Auth | Opis |
|--------|----------|------|------|
| `GET` | `/api/reviews/?book_slug=X` | AllowAny | Publiczna lista recenzji książki, paginowana (DRF default), najnowsze pierwsze |
| `PUT` | `/api/reviews/` | IsAuthenticated | Upsert na (user, book) z `{book_slug, body}` → 201 (created) / 200 (updated) |
| `GET` | `/api/reviews/me/?book_slug=X` | IsAuthenticated | Własna recenzja albo 404 |
| `DELETE` | `/api/reviews/<int:pk>/` | IsAuthenticated | Tylko własna (cudza → 403/404) |

Wzorzec PUT-upsert i kształt URL — kalka z `ratings/views.py` + `ratings/urls.py`.

### Gwiazdka autora przy recenzji

View anotuje queryset listy `Subquery` do `Rating` (OuterRef `user`+`book`) —
dokładnie wzorzec z `shelf/views.py:18`. Serializer publicznej listy zwraca:

```
id, body, created_at, updated_at,
author { handle, display_name },
author_rating: 1..5 | null     # SerializerMethodField z anotacji
```

### Wiring

- `"reviews.apps.ReviewsConfig"` w `INSTALLED_APPS` (`config/settings/base.py`).
- `path("api/", include("reviews.urls"))` w `config/urls.py`.

## Eksport danych

Dodać `reviews.json` do `users/exporters.py:build_user_export_zip` (lista
`{book_title, book_slug, body, created_at}`, `order_by("-created_at")`) + linia
w README.txt. Spójność z `shelf_entries.json` / `ratings.json`.

## Cleanup

Usunąć martwy `backend-django/reviews/__pycache__` (szczątek po PRE-M3) i
odbudować `reviews/` jako pełną apkę: `__init__.py`, `apps.py`, `models.py`,
`serializers.py`, `views.py`, `urls.py`, `migrations/`, `tests/`.

## Frontend

**API client** `svelte-frontend/src/lib/api/reviews.ts`:
- `getReviews(slug, page?)` → publiczna lista (paginowana)
- `getMyReview(slug)` → własna recenzja albo `null` (404 → null)
- `upsertReview(slug, body)` → PUT
- `deleteReview(id)` → DELETE

**Typy:** `Review` regenerowany z OpenAPI (`npm run types:api`), nie ręcznie.

**Komponenty** (`src/lib/components/review/`):

| Komponent | Rola |
|-----------|------|
| `ReviewCard.svelte` | autor (`display_name` / `@handle`) + jego gwiazdki (reużycie `RatingStars` read-only z `author_rating`) + `body` + data |
| `ReviewList.svelte` | lista kart + paginacja przez reużycie istniejącego `LoadMore` (wzorzec z `/discover`: przycisk „Load more" doklejający kolejną stronę). Bez infinite scroll, bez stron numerowanych. |
| `ReviewForm.svelte` | textarea + zapis; stan „napisz" vs „edytuj" + przycisk usuń, gdy własna istnieje |

**Strona** `/books/[slug]`:
- `+page.server.ts` — dołożyć ładowanie: publiczna lista (strona 1) + własna recenzja (jeśli zalogowany), dwa równoległe `fetch`.
- `+page.svelte` — nowa sekcja **„Reviews"** pod kontrolkami ratingu/shelf. Zalogowany: `ReviewForm` + `ReviewList`. Niezalogowany: tylko `ReviewList`.

Styl spójny z M3 (`ShelfControl`/`RatingStars`). Akcje przez synchroniczny `onclick`.

## Testy

**Backend** (`reviews/tests/`, `DJANGO_ENV=dev`):
- model: unique (user, book)
- PUT upsert: 201 przy tworzeniu, 200 przy edycji; walidacja pustego / za długiego `body`; 404 na zły `book_slug`
- `me`: 200 z recenzją / 404 bez / 401 bez auth
- DELETE: własna 204; cudza 403/404
- lista publiczna: AllowAny, paginacja, `author_rating` z joinu (z ratingiem i bez)
- aktualizacja `users/tests/test_data_export.py` o `reviews.json`

**Kontrakt API:** `make regenerate-openapi` → snapshot + `npm run types:api`;
`config/tests/test_openapi_schema.py` musi przejść.

**E2E** (Playwright):
1. zalogowany pisze recenzję → pojawia się na liście
2. edytuje → treść zaktualizowana
3. usuwa → znika
4. niezalogowany widzi listę, ale nie widzi formularza

## Poza zakresem (YAGNI)

Tytuł recenzji · spoiler-flag · lajki/komentarze do recenzji · moderacja ·
filtrowanie po `profile_public` · przeliczanie `avg_rating` z recenzji.
