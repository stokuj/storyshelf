# M12 — Social feed + reakcje (design)

> Status: spec. Gałąź `feat/m12-social-feed`. Zależy od M11 (Discover users + cudza półka).

## Cel

Domknięcie kierunku social po M11. Trzy deliverable:

1. **Feed aktywności obserwowanych** — `GET /api/feed/` (ocena / recenzja / skończona książka), liczony **w locie** z `Rating`/`Review`/`ShelfEntry`, bez modelu `Activity`.
2. **Polubienia recenzji** — `ReviewLike` (`POST/DELETE /api/reviews/{id}/like/`), `likes_count` + `is_liked` na `ReviewSerializer`.
3. **Publiczne recenzje na profilu** — `GET /api/u/{handle}/reviews/`, bramkowane `profile_public`.

Frontend: trasa `/feed` + sekcja „Reviews" na `/u/[handle]`.

## Decyzje (z brainstormingu)

| # | Decyzja | Wybór |
|---|---------|-------|
| Strategia feedu | on-the-fly merge vs model `Activity` | **on-the-fly** (merge 3 tabel w pamięci) — zero nowego schematu dla feedu, brak driftu/backfillu; trywialny koszt przy skali single-tenant |
| Typy aktywności | ocena / recenzja / skończona książka | wszystkie trzy |
| Dedup ocena+recenzja tej samej książki | scalać czy osobne wpisy | **osobne wpisy** (1a) — bez logiki łączenia |
| Czas „skończonej książki" | `finish_date` (DateField) nie ma godziny | **dodać `ShelfEntry.updated_at`** (DateTimeField, auto_now); sort feedu po nim, wyświetlać `finish_date` |
| Zakres feedu | własne aktywności? | **tylko obserwowani** (1a), bez własnych |
| Bramkowanie | aktywność prywatnych profili w feedzie? | **tylko `profile_public=True`** (2a) — spójne z resztą API |
| Lajk własnej recenzji | dozwolony? | **tak** (1a), bez `CheckConstraint` na self-like |
| Lajki w UI | gdzie | serce+licznik na `ReviewCard` wszędzie (profil + `/books/[slug]`); **feed bez przycisku lajka** |

## Sekcja 1 — Feed (`GET /api/feed/`)

Nowa app `feed/` — tylko widok + serializery, **zero modeli**. Endpoint **auth-only** (feed osobisty).

### Logika `feed/views.py`

1. `following_ids` = id obserwowanych przez `request.user`, przefiltrowane do `profile_public=True`.
2. Trzy zapytania, każde z cursorem `before` i limitem `page_size+1`:
   - `Rating.objects.filter(user__in=ids).select_related("user","book")` → sort `-updated_at`
   - `Review.objects.filter(user__in=ids).select_related("user","book")` → sort `-updated_at`
   - `ShelfEntry.objects.filter(user__in=ids, status=READ).select_related("user","book")` → sort `-updated_at`
3. Mapowanie każdego rekordu na dict wpisu (patrz niżej).
4. Scalenie w pamięci, sort malejąco po `timestamp`, ucięcie do `page_size`.
5. **Paginacja cursorowa:** query param `?before=<iso8601>` (domyślnie teraz). Odpowiedź `{results: [...], next_before: <timestamp ostatniego wpisu | null>}`. `next_before == null` → koniec.

`page_size = 20` (jak reszta API).

### Kształt wpisu

```json
{
  "type": "review",          // "rating" | "review" | "finished"
  "timestamp": "2026-06-05T12:00:00Z",
  "actor": {"handle": "ala", "display_name": "Ala", "avatar_url": "..."},
  "book": {"title": "Diuna", "slug": "diuna", "cover_url": "..."},
  "rating": null,            // type=rating; opcjonalnie author_rating dla review
  "body": "Świetna...",      // tylko review (może skrócony)
  "finish_date": null        // tylko finished
}
```

### Zmiana modelu

`ShelfEntry.updated_at = models.DateTimeField(auto_now=True)`. W dev reset DB (`flush --no-input && migrate`), bez ręcznych migracji. Nie zmieniamy typu `finish_date` (M9 stats zależą od `DateField` + `.year`).

Haczyk: `updated_at` ruszy się też przy zmianie `current_page`, ale dla statusu READ user zwykle już nie aktualizuje strony → w praktyce = czas skończenia. Akceptowalne.

## Sekcja 2 — Polubienia recenzji (`ReviewLike`)

### Model (`reviews/models.py`)

```python
class ReviewLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="review_likes")
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [UniqueConstraint(fields=["user", "review"], name="unique_user_review_like")]
```

Bez `CheckConstraint` na self-like.

### Endpoint

`@action(detail=True, methods=["post","delete"], permission_classes=[IsAuthenticated])` na `ReviewViewSet`:

- `POST /api/reviews/{id}/like/` → `get_or_create` (idempotentne, 201/200), zwraca `{likes_count, is_liked: true}`
- `DELETE /api/reviews/{id}/like/` → usuń jeśli istnieje (idempotentne, 204/200), zwraca `{likes_count, is_liked: false}`

Wzorzec idempotentny jak membership add/remove z M5.

### `ReviewSerializer`

- `likes_count` — annotacja `Count("likes")` w `get_queryset()` (nie property → bez N+1)
- `is_liked` — `Exists()` annotacja dla zalogowanego usera; gość/anon → `False`

Annotacje w `ReviewViewSet.get_queryset()` **oraz** w widoku publicznych recenzji (Sekcja 3), żeby `ReviewCard` miał komplet danych wszędzie.

### Frontend

`ReviewCard.svelte` — serce + licznik:
- gość: tylko licznik (read-only)
- zalogowany: klikalne serce, optymistyczny toggle z revertem na błąd (wzorzec `FollowButton` z M6; użyć `$state`, nie writable `$derived` — gotcha in-place mutation)

## Sekcja 3 — Publiczne recenzje na profilu

### Backend `GET /api/u/{handle}/reviews/`

Publiczny, read-only. Nowy `UserReviewListView`, zarejestrowany pod `api/u/<handle>/reviews/` w `config/urls.py` (obok `shelf/`, `shelves/`). Bramkowane `profile_public`: prywatny profil → `404` (spójnie z `PublicShelfEntryListView`). Recenzje danego usera, paginacja 20, sort `-updated_at`, z annotacjami `author_rating` + `likes_count` + `is_liked` (reuse `ReviewSerializer`).

### Frontend

1. **`/feed`** — nowa trasa, auth-only (redirect na login dla gości):
   - `+page.server.ts` ładuje pierwszą stronę `/api/feed/`
   - `FeedItem.svelte` renderuje wpis wg `type`, linki do książki i profilu aktora (reuse `Avatar`)
   - „Load more" po `next_before` (wzorzec LoadMore z M4)
   - `EmptyState` gdy pusto („Obserwuj kogoś, żeby zobaczyć aktywność")
   - link „Feed" w navbarze (obok „People" z M11)

2. **Sekcja „Reviews" na `/u/[handle]`** — pod sekcją „Reading" (M11):
   - ładuje `/api/u/{handle}/reviews/`, renderuje `ReviewCard` (z sercem/licznikiem z Sekcji 2)
   - „Load more", `EmptyState` gdy brak recenzji

## Zakres / YAGNI

Bez: powiadomień, komentarzy, repostów, modelu `Activity`, lajków obiektów innych niż recenzje.

## Testy

- **Backend:** feed (merge + cursor + bramkowanie prywatnych + tylko obserwowani), `ReviewLike` (idempotencja, własna recenzja, `likes_count`/`is_liked`), publiczne recenzje (404 dla prywatnego). Regeneracja OpenAPI snapshot (`make regenerate-openapi`).
- **E2E:** feed pokazuje aktywność obserwowanego, lajk recenzji toggle, sekcja recenzji na profilu.
