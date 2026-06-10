# Audit fixes — spec (design)

> Status: do recenzji. Gałąź: `chore/holistic-audit` (kontynuacja).
> Źródło: `2026-06-09-holistic-audit-report.md` (tylko pozycje confirmed).
> Następny krok po akceptacji: `/writing-plans`.

## Cel

Naprawić 24 potwierdzone findings z holistycznego audytu. Bez nowych funkcji.
Baseline przed zmianami: 388 testów backend, svelte-check/lint/openapi zielone.

## Blocker

### B1. CI: gating build-and-push

`.github/workflows/ci.yml` — job `build-and-push` dostaje `needs: [lint, test, frontend]`
(nazwy jobów potwierdzić w pliku). Bez tego zepsuty main publikuje obrazy do ghcr.io.
**Weryfikacja:** YAML poprawny (CI na PR przejdzie); push obrazów odpala się dopiero po zielonych jobach.

## Important

### I1. Parytet prod po M13 (infra)

- `infra/compose/docker-compose.prod.yml`: dodać `redis` i `celery` (wzór z dev.yml, bez
  dev-only montowań), `restart: unless-stopped` także dla `django`.
- `infra/.env.example`: dodać `CELERY_BROKER_URL=redis://redis:6379/0`,
  `CELERY_RESULT_BACKEND=redis://redis:6379/0` + skomentowane `THROTTLE_*` (z I-nit N6).
- `infra/caddy/Caddyfile`: `handle /media/* { reverse_proxy django:8000 }` i analogicznie
  `/static/*` (kolejność przed catch-all).

**Weryfikacja:** `docker compose -f docker-compose.prod.yml config` przechodzi; Caddyfile
poprawny składniowo (`caddy validate` lub review).

### I2. BookAdmin: pola liczone read-only

`books/admin.py`: `readonly_fields = ("avg_rating", "ratings_count")`.
**Weryfikacja:** test admin lub ręcznie; istniejące testy zielone.

### I3. `make verify` działa z hosta

Makefile: zmienna `VERIFY_DATABASE_URL ?= postgres://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@localhost:5432/$(POSTGRES_DB)`
z wartościami wczytanymi z `infra/.env` (Makefile już zna ENV_FILE); kroki
pytest/manage.py test w `verify` dostają `DATABASE_URL=$(VERIFY_DATABASE_URL)`.
Do tego notka w CLAUDE.md (Komendy), że testy z hosta wymagają żywej dev-DB (`make dev-up`).
**Weryfikacja:** `make verify` na czysto przechodzi end-to-end.

### I4. Sync dokumentacji (CLAUDE.md / ROADMAP / ARCHITECTURE / ADR / docs/api)

- **CLAUDE.md:** „Bez AI/Celery — 3 kontenery" → stan po M13 (5 kontenerów dev; prod bez
  redis/celery do wdrożenia — po I1 już z nimi, dopasować treść do wyniku I1); lista apps
  + `feed`, `characters`; komentarz `make dev-up`.
- **ROADMAP:** „Aktualny krok" → brak aktywnego milestone, M13 zmergowane (PR #77);
  wiersz M14 w „Zrobione" (PR #78, typed relations); M13 wiersz z numerem PR; „Po
  M11–M13" → „Po M11–M14"; w „Kiedyś": usunąć „karty postaci, graf relacji" z pozycji AI
  (zostają tematy/ton, pgvector), etykietę „M14" przy homepage → „kolejny milestone";
  dopisać do „Kiedyś": edycja `bio` z UI; do punktu wdrożenia: ALLOWED_HOSTS z domeną,
  non-root w Dockerfile'ach.
- **ARCHITECTURE:** API surface + `GET /api/users/`, `GET /api/u/{handle}/shelf/`;
  nagłówek „M1–M14"; `CharacterRelation` z `relation_type`; `ShelfEntry` + `finished_at`;
  `avatar_url` → `avatar` w opisie modelu; Book + `ratings_count`; diagram kontenerów —
  stan po I1. (auth/me: patrz I9 — po usunięciu nie dopisujemy.)
- **ADR-001:** ścieżki refresh → `/api/auth/refresh/` (2 miejsca).
- **ADR-003:** notka, że throttle `character_generate` 10/h wdrożony (f524d53) — ryzyko domknięte.
- **docs/api/README.md:** usunąć terminologię „Phase 2.0/3.0".

**Weryfikacja:** grep po starych frazach pusty; linki/ścieżki istnieją.

### I5. E2E: seed brakujących książek

`e2e/global-setup.ts`: dodać `The Hobbit` (slug `the-hobbit`, page_count 423) i
`The Two Towers` (slug `the-two-towers`) do seedu — `shelf-status.spec.ts` i
`reviews.spec.ts` przestają zależeć od zastanej lokalnej DB. (Alternatywa — przepisanie
speców na `.seed-slugs.json` — większy diff, nie wybieramy.)
**Weryfikacja:** `npx playwright test shelf-status reviews` na bieżącej DB zielone.

### I6. `/users`: obsługa loadError

`routes/users/+page.svelte`: czytać `loadError` z `data` i pokazać toast (wzorzec z
`discover/+page.svelte`).
**Weryfikacja:** svelte-check; ręcznie/E2E nie wymagane.

### I7. Phantom controls: usunąć

- `settings/profile/+page.svelte`: usunąć 3 switche (`show_real_name`, `show_activity`,
  `indexed_by_search_engines`) — backend ich nie ma (YAGNI; wrócą z backendem, jeśli kiedyś).
- `settings/+page.svelte`: usunąć statyczny pasek „Password strength" (hardcoded 25%).

**Weryfikacja:** svelte-check + lint; formularz privacy nadal zapisuje `profile_public`.

### I8. Feedback formularzy settings

`settings/+page.svelte` i `settings/profile/+page.svelte`: czytać `form` (wynik akcji)
i pokazywać błąd (`form.error`) oraz sukces (toast „Saved" — wzorzec sonner jak w reszcie
apki). Dotyczy akcji: profile, handle, email, password, privacy.
**Weryfikacja:** ręcznie: błędne current password → komunikat; sukces → toast.

### I9. Usunąć martwy endpoint `GET /api/auth/me/`

`users/urls/auth.py` (path `me/`), `AuthMeView` w views + powiązane testy; front używa
`/users/me/`. `make regenerate-openapi` + kontrakt-test.
**Weryfikacja:** testy users zielone; grep `auth/me` pusty (kod+docs).

### I10. Kontrakt TS: rozdzielić typy Book i PublicShelfEntry

- `lib/types/book.ts`: `BookListItem` (pola `BookListSerializer`, z `id`) i `BookDetail`
  (pola `BookDetailSerializer`, bez `id`); `listBooks` → `PaginatedResponse<BookListItem>`,
  `getBook` → `BookDetail`; poprawić użycia (minimalny diff — większość miejsc używa pól wspólnych).
- `lib/types/shelf.ts` + `api/shelf.ts`: typ `PublicShelfEntry` (bez `id`) dla
  `fetchPublicShelf`.
- Przy okazji (z tego samego pliku): usunąć martwy typ `Author`.

**Weryfikacja:** svelte-check 0 errors.

### I11. `books.ts`: parametr `isServerSide` zamiast hardcode

`listBooks`/`getBook`/`fetchGenres` przyjmują `isServerSide = false` jak reszta API,
load functions przekazują `true`; wywołania client-side (discover load-more, search)
przechodzą na `/api` same-origin.
**Weryfikacja:** svelte-check; ręcznie: load-more na `/discover` działa.

### I12. Chip filtra autora na `/discover`

Gdy `currentAuthor !== ''`: widoczny chip „Author: {name} ×" (zdjęcie filtra czyści
`?author=`). Domyka klasę „ślepy zaułek" z M10.
**Weryfikacja:** ręcznie: wejście z linku autora → chip widoczny, × czyści filtr.

## Nit (zgrupowane w paczki)

### N1. Testy characters + feed + ratings

- characters: re-dispatch po DONE i FAILED (`delay` wywołany), brak dispatchu przy
  PENDING, lista ze `status=null` bez analizy, 404 dla złego `char_slug`, asercja
  RUNNING w trakcie taska (side_effect czytający DB), `choices: []` i `content="[]"` w ai.
- feed: `?before=garbage` → 400; asercja kształtu itemu (`book`/`body`/`rating`).
- ratings: DELETE cudzej oceny → 404.

**Weryfikacja:** nowe testy failują przed/przechodzą po (tu: kod już poprawny, więc
testy od razu zielone — wystarczy, że asercje są realne); pełny suite zielony.

### N2. A11y paczka (frontend)

Dropdown: `role="menu"` na content, `aria-haspopup`/`aria-expanded` na triggerze;
dialog delete: `aria-labelledby` + zamykanie Escape; tablisty `/shelf`: `aria-controls`
+ `role="tabpanel"`/`id`; `RelationGraph`: `<title>`/`aria-label` na `<svg>`.
**Weryfikacja:** svelte-check/lint; ręczny smoke dropdownów.

### N3. Frontend drobiazgi

`npm uninstall @xyflow/svelte sveltekit-superforms`; `fetchGenres` w `$effect` z obsługą
błędu (toast); `ComponentType` → `Component` w `EmptyState`; migracja `$app/stores` →
`$app/state` (8 plików); `FilterBar` outside-click przez `bind:this` + `contains` zamiast
`closest('.relative')`.
**Weryfikacja:** svelte-check 0 errors, lint clean, build przechodzi.

### N4. Backend drobiazgi

Brak `book_slug` w PUT rating/review → 400 z komunikatem (przed lookupem); 
`FeedBookSerializer.cover_url` → `CharField(allow_blank=True)` (model nigdy null);
usunąć redundantny `userfollow_following_idx` (FK ma index; migracja); komentarz przy
rozjeździe sortowania recenzji (profil `-updated_at` celowo „ostatnio edytowane");
`GenerateCharactersView`: `transaction.atomic()` + `select_for_update` na analysis;
`min_length` hasła 6 → 8 (register + password change; front już wymaga 8).
**Weryfikacja:** testy backend zielone (nowe asercje dla 400 i min_length); openapi
regen jeśli schema się zmieni.

### N5. OpenAPI nullability

`@extend_schema_field` (nullable) na 4× `get_avatar_url` w `users/serializers.py` i na
`BookDetail.serie`; `make regenerate-openapi`; kontrakt-test zielony.
**Weryfikacja:** w openapi.yml `avatar_url`/`serie` mają `nullable: true`.

### N6. Infra drobiazgi

Nowy `svelte-frontend/.dockerignore` (node_modules, .svelte-kit, build, e2e,
test-results, playwright-report, .env*); rozszerzyć `backend-django/.dockerignore`
(`**/__pycache__/`, `media/`, `.pytest_cache/`); usunąć komentarz `phase/2.6` z ci.yml;
usunąć martwy `CELERY_WORKER_CONCURRENCY` z base.py (CLI flag rządzi) lub podpiąć w
compose — wybieramy usunięcie; `THROTTLE_*` jako skomentowane przykłady w `.env.example`
(ujęte w I1); ujednolicić runner testów: CI przechodzi na `pytest` (jak Makefile).
**Weryfikacja:** CI zielone po zmianie; docker build działa.

## Kolejność

1. B1 (CI gating) — natychmiast, niezależne.
2. I2, I9, N4, N5 (backend) → regen OpenAPI raz na końcu paczki.
3. I10, I11, N3 (frontend typy/API) → potem I6, I7, I8, I12, N2 (frontend UI).
4. I1, I3, N6 (infra/tooling).
5. N1 (testy — po zmianach backendu, żeby objąć nowe 400/min_length).
6. I5 (E2E seed) + przebieg E2E.
7. I4 (docs — na końcu, opisuje stan po zmianach).

## Weryfikacja końcowa

`make verify` end-to-end (po I3 działa z hosta) + `npx playwright test` + przebieg
ręczny: settings (feedback/phantom), /discover (chip autora, load-more), /users (error toast).

## Granice

Bez zmian w: throttlingu poza istniejącym, paginacji follow/ratings, deploy prod
(poza parytetem compose z I1), E2E characters. Odrzucone pozycje — patrz raport.
