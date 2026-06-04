# M11 — Discover users + cudza półka (design)

> Status: zatwierdzone 2026-06-04. Gałąź `feat/m11-user-discovery`.

## Cel

Umożliwić *znalezienie* innych czytelników i podejrzenie, co czytają. Domyka M6 Follow:
dziś można kogoś obserwować, ale nie ma jak go znaleźć ani zobaczyć jego aktywności.

## Zakres

Dwa nowe endpointy read-only + frontend `/users` i sekcja „Reading" na publicznym profilu.

### Decyzje (zatwierdzone)

| # | Decyzja | Wybór |
|---|---------|-------|
| D1 | Dostęp do `/users` i `/api/users/` | Publiczny (`AllowAny`); follow tylko zalogowany (już obsłużone w M6) |
| D2 | Domyślne sortowanie listy + search | `-followers_count` (most-followed), przełącznik „newest" (`-created_at`); search po `handle`+`display_name` |
| D3 | Wiersz na `/users` | Reuse `UserRow` + opcjonalne „X followers"; follow dopiero po wejściu w profil (bez inline-follow) |
| D4 | Zakres publicznej półki | Wszystkie statusy (Want/Reading/Read), read-only, status widoczny, + ocena autora |

Dodatkowo: publiczna półka = **tylko domyślna `ShelfEntry`** (custom półki M5 zostają jak są).
Publiczna półka **bez paginacji** (jak własny `/shelf`); `/users` paginowane.

## Backend

### 1. `GET /api/users/` — lista publicznych profili

- **Routing:** `users/urls/users.py`, `path("", UserListView.as_view())`. `""` nie koliduje
  ze stringowymi trasami `me/...`.
- **View:** `UserListView(generics.ListAPIView)`, `permission_classes = (AllowAny,)`,
  `pagination_class = StandardPagination` (20/stronę, kształt `{data,page,per_page,total}`).
- **Queryset:**
  ```python
  User.objects.filter(profile_public=True).annotate(
      followers_count=Count("follower_set", distinct=True)
  )
  ```
- **Filtry:** DRF `SearchFilter` (`search_fields = ["handle", "display_name"]` → `?search=`)
  + `OrderingFilter` (`ordering_fields = ["followers_count", "created_at"]`,
  `ordering = ["-followers_count", "handle"]` jako default — `handle` to stabilny tiebreak).
- **Serializer `UserListSerializer`:** `handle`, `display_name`, `avatar_url`
  (`SerializerMethodField`, `request.build_absolute_uri` jak w innych serializerach),
  `followers_count` (`IntegerField(read_only=True)`).
- Zalogowany user widzi też siebie, jeśli ma `profile_public=True` (bez special-case).

### 2. `GET /api/u/{handle}/shelf/` — publiczna domyślna półka

- **Routing:** `config/urls.py`, `path("api/u/<str:handle>/shelf/", PublicShelfEntryListView.as_view())`
  — obok istniejącego `path("api/u/<str:handle>/shelves/", include("shelf.urls_public"))`.
- **View** (w `shelf/views.py`): `PublicShelfEntryListView(generics.ListAPIView)`,
  `permission_classes = (AllowAny,)`, `pagination_class = None`.
  - Owner przez istniejący `_public_owner_or_404(self.request, self.kwargs["handle"])`
    (reuse — bramkuje `profile_public`, 404 dla prywatnych / nieistniejących).
  - Queryset (wzorzec z `ShelfEntryViewSet.get_queryset`):
    ```python
    owner = _public_owner_or_404(self.request, self.kwargs["handle"])
    user_rating = Rating.objects.filter(
        user=OuterRef("user"), book=OuterRef("book")
    ).values("rating")[:1]
    return (
        ShelfEntry.objects.filter(user=owner)
        .annotate(user_rating=Subquery(user_rating))
        .select_related("book")
        .prefetch_related("book__authors", "book__genres")
        .order_by("-created_at")
    )
    ```
- **Serializer `PublicShelfEntrySerializer`** (read-only): `book` (reuse `ShelfBookSerializer`),
  `status`, `start_date`, `finish_date`, `current_page`, `user_rating`
  (`SerializerMethodField` → `getattr(obj, "user_rating", None)`, `@extend_schema_field(IntegerField(allow_null=True))`).

## Frontend

| Plik | Zmiana |
|------|--------|
| `lib/api/user.ts` | dodać `listUsers(fetch, {search, ordering, page, perPage})` zwracające stronę (`{data,page,per_page,total}`) + typ `UserListItem` (`handle`, `display_name`, `avatar_url`, `followers_count`) |
| `lib/api/shelf.ts` | dodać `fetchPublicShelf(fetch, handle, ssr)` → `/u/{handle}/shelf/` (zwraca `ShelfEntry[]`) |
| `lib/components/UserRow.svelte` | rozluźnić typ propa `user` do `{ handle: string; display_name: string; avatar_url: string \| null }` (wspólny podzbiór `FollowUser` i `UserListItem`) + opcjonalny `followersCount?: number` → render „{n} followers" tylko gdy podany. Nie zmienia działania followers/following (nie podają licznika) |
| `routes/users/+page.server.ts` | load listy z `search`/`ordering`/`page` z `url.searchParams` (wzorzec jak `/discover`) |
| `routes/users/+page.svelte` | search box + przełącznik sortowania (Most followed / Newest) + lista `UserRow` (z `followersCount`) + paginacja |
| `routes/u/[handle]/+page.server.ts` | dołożyć `fetchPublicShelf(fetch, params.handle, true)` do load (obok profilu i półek) |
| `routes/u/[handle]/+page.svelte` | sekcja „Reading" — lista wpisów (okładka + tytuł + autor + badge statusu + ★ocena gdy jest), link do `/books/[slug]`; sekcja ukryta gdy pusto (jak „Shelves") |
| `lib/components/shell/AppShell.svelte` | link „People" → `/users` w nav (zawsze widoczny — endpoint publiczny) |

Sekcja „Reading" jako jedna lista (newest first) ze statusem na wpisie — bez grupowania per-status.

## Testy

- **Backend** (`users/tests/`, `shelf/tests/`, DRF `APITestCase`):
  - Lista: prywatni odfiltrowani; `?search=` po handle i display_name; `?ordering=-created_at`;
    domyślne sortowanie most-followed; kształt paginacji `{data,page,per_page,total}`.
  - Publiczna półka: zwraca wpisy właściciela ze wszystkich statusów + `user_rating`;
    prywatny profil → 404; nieistniejący handle → 404; kolejność `-created_at`.
- **Kontrakt OpenAPI:** `make regenerate-openapi` po dodaniu tras (2 nowe ścieżki), test
  `config/tests/test_openapi_schema.py` zielony.
- **E2E** `e2e/users.spec.ts` (~3 scenariusze): lista pokazuje seedowanego usera →
  `?search=` filtruje → klik wiersza → publiczny profil → widoczna sekcja „Reading".

## Obsługa błędów

- Publiczna półka prywatnego/nieistniejącego usera → 404 (`_public_owner_or_404`).
- Lista z pustym wynikiem search → `data: []` (200).

## Granice (YAGNI)

- Bez inline-follow w wierszach listy.
- Bez grupowania publicznej półki per-status.
- Bez paginacji publicznej półki.
- Bez podglądu custom-półek tutaj (są już na profilu z M5).
- Bez zmian w modelach — wyłącznie nowe widoki/serializery/trasy + frontend.
