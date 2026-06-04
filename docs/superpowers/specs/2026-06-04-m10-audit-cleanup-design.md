# M10 — Audyt / fix / cleanup (design / spec)

> Status: zatwierdzony 2026-06-04. Gałąź: `chore/m10-audit-cleanup`.
> Ostatni milestone przed wdrożeniem produkcyjnym (wdrożenie = osobno, „Po M10").
> Następny krok: `/writing-plans`.

## Cel

Domknąć fazę post-MVP: naprawić znalezione w audycie niespójności, usunąć martwy kod,
zsynchronizować dokumentację ze stanem po M6–M9. Bez nowych funkcji.

## Kontekst audytu (2026-06-04)

Audyt subagentami **nowego kodu M6 (follow) + M9 (stats)** → **czysto** (zero blockerów/
important; backend 173 testy zielone + ruff clean, frontend check/lint clean). Następnie
przegląd spójności **całej apki** wykrył dwie instancje klasy „linkowalne dane renderowane
jako ślepy zaułek" oraz niespójność prefiksów API i jedno martwe pole.

NIT-y backendu pozostawione świadomie (intencjonalne, udokumentowane): stale `finish_date`
przy round-tripie statusu, `time_on_shelf_days` liczone od `created_at` (nie `start_date`).

Poza zakresem (ROADMAP): lista userów `/users`, spersonalizowany homepage (→ „Kiedyś");
konfiguracja wdrożenia — deploy step `ci.yml`, Caddy/Let's Encrypt, sekrety,
`CORS_ALLOWED_ORIGINS`, `JWT_COOKIE_DOMAIN` (→ „Po M10").

## Zakres prac

### 1. ReviewCard: autor → link do profilu

`svelte-frontend/src/lib/components/review/ReviewCard.svelte` — nazwa autora to dziś zwykły
`<span>` (`review.author.display_name || @handle`), mimo że `review.author.handle` jest w
typie. Owinąć w `<a href="/u/{review.author.handle}">` (zachować fallback display_name→@handle).
To domyka pętlę odkrywania: książka → recenzja → profil autora → follow.

**Weryfikacja:** istniejące E2E recenzji nie mogą się wywrócić; ręcznie/E2E: klik w autora
prowadzi na `/u/{handle}`.

### 2. BookHeader: gatunki → link do filtrowanego /discover

`svelte-frontend/src/lib/components/book/BookHeader.svelte` — autorzy linkują do
`/discover?author=…`, ale gatunki to nielinkowane `<Badge>`. `/discover` czyta `?genre=`
z URL (potwierdzone). Owinąć badge gatunku w `<a href="/discover?genre={encodeURIComponent(genre)}">`
(spójnie z autorami). Zachować wygląd Badge.

### 3. Konsolidacja prefiksu API follow: `/api/users/{handle}/…` → `/api/u/{handle}/…`

Dziś follow leży pod `/api/users/{handle}/follow|followers|following/` (`users/urls/users.py`),
a profil publiczny i półki pod `/api/u/{handle}/…`. To ten sam zasób „user po handle" pod
dwoma prefiksami. Ujednolicić pod `/api/u/`.

- **Backend:** przenieść 3 ścieżki (`<handle>/follow/`, `<handle>/followers/`,
  `<handle>/following/`) z `users/urls/users.py` do `users/urls/public.py` (włączane przy
  `api/u/`). Umieścić je **przed** catch-all `<str:handle>/` (profil). Widoki i ich
  permissiony bez zmian (`UserFollowView` auth-only, `FollowListView` AllowAny gated 404).
  Usunąć nieużywane importy w `users/urls/users.py`.
- **Frontend:** `svelte-frontend/src/lib/api/follow.ts` — zmienić 3 ścieżki z
  `/users/${handle}/…` na `/u/${handle}/…`.
- **Testy:** `backend-django/users/tests/test_users.py` — zaktualizować URL-e follow na `/api/u/…`.
- **OpenAPI:** `make regenerate-openapi`; kontrakt-test zielony.

**Granica:** nie ruszamy `/api/users/me/…` (to „ja", nie „user po handle" — zostaje).

### 4. Usunąć martwe pole `total_books`

`totals.total_books` jest wystawiane przez API, ale **nigdzie nierenderowane** na froncie
(istnieje tylko w typie TS). Usunąć:
- `backend-django/users/stats.py` — pole `total_books` z `totals`.
- `backend-django/users/serializers.py` — pole z `_StatsTotalsSerializer`.
- `backend-django/users/tests/test_stats.py` — asercje na `total_books`.
- `svelte-frontend/src/lib/api/stats.ts` — pole z typu `UserStats.totals`.
- `make regenerate-openapi`; kontrakt-test zielony.

### 5. Sync `docs/ARCHITECTURE.md`

Zaktualizować, by odzwierciedlało stan po M6–M9:
- **API surface:** dodać `GET /api/users/me/stats/`; follow endpointy pod nowym prefiksem
  `/api/u/{handle}/follow|followers|following/`; zaznaczyć profil annotuje
  `followers_count`/`following_count`/`is_following`.
- **App `users/`:** wzmianka o reading stats (`users/stats.py::build_user_stats`).
- **Frontend:** dodać trasę `/stats`.
- Sprawdzić, że nic nie odwołuje się do usuniętego `GOAL.md` (audyt: brak — potwierdzić po edycjach).

### 6. Sync `docs/ROADMAP.md`

- M9 → sekcja „Zrobione" (zmergowane PR #72).
- „Aktualny krok" → M10 w toku (audyt/cleanup), potem wdrożenie.
- M10 zniknie z „Następne" po zakończeniu (osobny commit usuwający spec/plan wg konwencji).

## Kolejność / izolacja

Każdy punkt jest niezależny i samodzielnie testowalny. Sugerowana kolejność (od najmniej do
najbardziej dotykającego):
1. #4 total_books (backend+front+OpenAPI) — wąskie.
2. #3 prefiks API (backend+front+testy+OpenAPI) — najszersze, ale izolowane.
3. #1 ReviewCard link, #2 BookHeader genre link — frontend, drobne.
4. #5 ARCHITECTURE.md, #6 ROADMAP.md — docs na końcu (po ustabilizowaniu API).

## Testy / weryfikacja

- Backend: `DJANGO_ENV=dev … manage.py test` (po #3/#4: `users`, `shelf`, `config` zielone),
  `ruff check .` clean, kontrakt OpenAPI zielony po każdej regeneracji.
- Frontend: `npm run check` (0 errors), `npm run lint` clean.
- E2E (jeśli dotyczy follow): URL-e follow zmienione → potwierdzić `e2e/follow.spec.ts` przechodzi
  (korzysta z `follow.ts`, więc powinno działać bez zmian w teście).
- Smoke: klik autora recenzji → `/u/{handle}`; klik gatunku → `/discover?genre=`.

## Zakres / granice (czego NIE robimy)

- Brak zmian funkcjonalnych (żadnych nowych ekranów/endpointów).
- Nie ruszamy NIT-ów backendu (stale finish_date, time-on-shelf basis) — intencjonalne.
- Nie konfigurujemy wdrożenia (osobna faza „Po M10").
- Nie dodajemy listy `/users` ani homepage'a (→ „Kiedyś").
- `/api/users/me/*` bez zmian.
