# Holistyczny audyt — raport (2026-06-09/10)

> Wykonany wg `2026-06-09-holistic-audit-design.md`. Faza 1: 5 agentów obszarowych (Sonnet),
> faza 2: agent kontraktu API + agent „phantom UI" (Sonnet). Każdy finding zweryfikowany
> w kodzie przez głównego agenta (adjudykacja). Werdykty: ✅ confirmed → spec fixów ·
> 🚫 wontfix (realne, ale świadomie nie naprawiamy — uzasadnienie) · ❌ false-positive ·
> 📌 intentional (udokumentowana decyzja) · ⏭ out-of-scope.

## Baseline (krok 0)

- `ruff check` — clean; `manage.py check` — clean.
- Backend pytest: **388 passed** (z hosta wymaga `DATABASE_URL=postgres://postgres:…@localhost:5432/booksdb` — bez tego 370 errors; samo w sobie zgłoszone jako finding #4).
- OpenAPI snapshot test, `svelte-check`, `eslint/prettier` — zielone (dokończone osobno po przerwaniu `make verify` na kroku pytest).

## Findings — confirmed (idą do specki fixów)

| # | Obszar | Finding | Waga po adjudykacji |
|---|--------|---------|------|
| 1 | CI | `build-and-push` w `ci.yml` bez `needs: [lint, test, frontend]` — obrazy pushowane do ghcr.io nawet gdy testy padają | **Blocker** |
| 2 | Infra | Dryf prod po M13: prod compose bez `redis`/`celery`, `.env.example` bez `CELERY_BROKER_URL`/`CELERY_RESULT_BACKEND`, django bez `restart: unless-stopped`, Caddyfile bez `handle /media/*` i `/static/*` (avatary i CSS admin/Swagger martwe w prodzie) | Important |
| 3 | Backend | `BookAdmin` pozwala edytować `avg_rating`/`ratings_count` (pola liczone sygnałem) — brak `readonly_fields` | Important |
| 4 | Tooling | `make verify` (pytest z hosta) pada bez `DATABASE_URL` — 370 errors na świeżym środowisku; gotcha znana tylko z memory, nie z repo | Important |
| 5 | Docs | CLAUDE.md: „Bez AI/Celery — 3 kontenery" (nieprawda od M13), lista apps bez `feed`/`characters`, komentarz `dev-up` | Important |
| 6 | Docs | ROADMAP: „Aktualny krok" sprzed merge M13 (PR #77), brak wpisu M14 (PR #78), M13 bez numeru PR, „Po M11–M13", mylący „M14" przy homepage w Kiedyś, „karty postaci, graf relacji" wciąż w Kiedyś | Important |
| 7 | Docs | ARCHITECTURE: brak `GET /api/users/`, `GET /api/u/{handle}/shelf/`, `GET /api/auth/me/`; nagłówek „M1–M13"; `CharacterRelation` bez `relation_type`; `ShelfEntry` bez `finished_at`; `avatar_url` zamiast `avatar`; Book bez `ratings_count`; diagram redis/celery bez noty „dev only" | Important |
| 8 | Docs | ADR-001: ścieżka refresh cookie `path=/api/users/token/refresh/` ×2 — rzeczywista to `/api/auth/refresh/`; ADR-003: „throttle odłożony na później" — wdrożony (`character_generate` 10/h, f524d53) | Important |
| 9 | Testy/E2E | `shelf-status.spec.ts` i `reviews.spec.ts` zależą od slugów `the-hobbit`/`the-two-towers`, których `global-setup.ts` nie seeduje (działa tylko na starej lokalnej DB) | Important |
| 10 | Frontend | `/users` ignoruje `loadError` z serwera — awaria API wygląda jak pusty katalog (wzorzec toastu z `/discover` istnieje) | Important |
| 11 | Frontend | Phantom controls: 3 switche privacy w `settings/profile` bez backendu + statyczny pasek „Password strength: Weak" (25% hardcoded) | Important |
| 12 | Frontend | Formularze `/settings` i `/settings/profile` nie pokazują ŻADNEGO feedbacku — `fail()` z akcji i sukces są ignorowane (nikt nie czyta `form`) | Important |
| 13 | Frontend | `books.ts`: `listBooks`/`getBook`/`fetchGenres` mają hardcoded `isServerSide=true` — client-side działa przypadkiem (fallback do `PUBLIC_API_URL`) | Important |
| 14 | Kontrakt | Typ TS `Book` współdzielony między list/detail: detail nie zwraca `id` (TS twierdzi że jest), list nie zwraca 9 pól deklarowanych jako wymagane; `PublicShelfEntry` reużywa `ShelfEntry` z phantom `id` | Important |
| 15 | Kontrakt | `GET /api/auth/me/` — martwy endpoint (front używa `/users/me/`); usunąć lub udokumentować | Important |
| 16 | Frontend | Filtr `?author=` na `/discover` jest niewidzialny — brak chipa/badge z możliwością zdjęcia (klasa „ślepy zaułek" jak w M10) | Important |
| 17 | Testy | Luki characters: brak testu re-dispatch po DONE/FAILED, idempotencji przy PENDING, `status=null` przy braku analizy, 404 dla złego `char_slug`, asercji RUNNING w tasks, `choices: []` i `content="[]"` w ai | Nit |
| 18 | Testy | `feed`: brak testu `?before=garbage` → 400; brak asercji kształtu itemu; `ratings`: brak testu DELETE cudzej oceny → 404 | Nit |
| 19 | Frontend a11y | Paczka: dropdown bez `role="menu"`/`aria-expanded`/`aria-haspopup`, dialog delete bez `aria-labelledby`/Escape, tablisty na `/shelf` bez `aria-controls`/`tabpanel`, SVG grafu bez etykiety | Nit |
| 20 | Frontend | Martwe: deps `@xyflow/svelte` + `sveltekit-superforms` (0 importów), typ `Author` (0 użyć, niezgodny z serializerem) | Nit |
| 21 | Frontend | `fetchGenres` w `$effect` bez catch (cicha utrata listy); `ComponentType` deprecated → `Component`; `$app/stores` → `$app/state` (8 plików); `FilterBar` outside-click po `.relative` łapie cudze elementy → element refs | Nit |
| 22 | Backend | Drobiazgi: brak `book_slug` w PUT rating/review → 404 zamiast 400; `FeedBookSerializer.cover_url` `allow_null` → `allow_blank`; redundantny index `userfollow_following_idx` (FK ma własny); rozjazd sortowania recenzji (`-created_at` vs `-updated_at`) — komentarz lub ujednolicenie; race w `GenerateCharactersView` (podwójny dispatch → podwójny koszt LLM; stan końcowy spójny) — `transaction.atomic` + `select_for_update`; `min_length` hasła 6 (backend) vs 8 (front) — ujednolicić na 8 | Nit |
| 23 | Kontrakt | OpenAPI kłamie o nullability: `avatar_url` ×4 (`SerializerMethodField` bez `@extend_schema_field`) i `BookDetail.serie` — realnie `null`, schema mówi `nullable: false`; po fixie `make regenerate-openapi` | Nit |
| 24 | Infra | Drobiazgi: brak `svelte-frontend/.dockerignore` (node_modules w build context), rozszerzyć backendowy; martwy komentarz `phase/2.6` w ci.yml; martwy setting `CELERY_WORKER_CONCURRENCY` (CLI `--concurrency=4` nadpisuje); throttle env vars nieudokumentowane w `.env.example`; CI `manage.py test` vs Makefile `pytest` — ujednolicić | Nit |

## Findings — odrzucone (z uzasadnieniem)

| Obszar | Zgłoszenie | Werdykt |
|--------|-----------|---------|
| Backend | Brak paginacji `FollowListView` / brak throttle na write endpoints (rating/review/like/shelf/avatar/feed) | 🚫 wontfix — wszystkie auth-only; skala single-tenant (ROADMAP „Czego NIE robimy: >10k"); throttling celowo tylko auth + `character_generate` (koszt LLM) |
| Backend | Pętla `get_or_create` przy blackliście tokenów w PasswordChange | 🚫 wontfix — liczba sesji per user ograniczona lifetime'em refresh tokena; bulk_create to optymalizacja bez problemu |
| Backend | `review.likes.count()` jako zbędne zapytanie | 🚫 wontfix — jeden COUNT na akcję like'a, koszt pomijalny |
| Backend | `RatingViewSet` bez paginacji | 📌 intentional — komentarz w kodzie („plain list (own ratings)") |
| Backend | `CharacterAnalysis.model` max_length=200 za krótkie | ❌ false-positive — nazwy modeli OpenRouter ~30 znaków; spekulacja |
| Backend | Slug TOCTOU w books/shelf | 🚫 wontfix — retry-pętla w `save()` jest świadomym, udokumentowanym komentarzem zabezpieczeniem; skala nie uzasadnia locków |
| Frontend | Komponenty używają globalnego `fetch` zamiast DI | ❌ false-positive — client-side `fetch` + `credentials:'include'` z `_client.ts` jest poprawny; agent sam to przyznał |
| Frontend | `confirm()` vs custom dialog — niespójność | 🚫 wontfix — oba działają; unifikacja to polish bez wartości teraz |
| Frontend | Dark/Light bez wskaźnika aktywnego trybu | 🚫 wontfix — drobny UX polish |
| Frontend | `let {} = $props()` workaround w settings | 🚫 wontfix — działa, ujednolicenie kosmetyczne |
| Kontrakt | `/api/authors/`, `/api/series/`, `/api/tags/` bez konsumenta front | 📌 intentional — read-only library API z M2, udokumentowane w ARCHITECTURE |
| Kontrakt | TS `string \| null` dla pól nigdy-null (`cover_url`, `description`, `bio`); `SerieInfo.status` bez `\| null`; follow/generate return types szersze/węższe | 🚫 wontfix — nieszkodliwe (front traktuje `""`/`null` identycznie); zaciskanie typów bez zysku |
| Kontrakt | Brak UI edycji `bio` mimo wsparcia w PATCH | ⏭ out-of-scope — gap funkcjonalny, kandydat do ROADMAP „Kiedyś", nie fix |
| Testy | Brak E2E dla characters | 🚫 wontfix — sekcja wymaga danych z LLM, których E2E nie zaseeduje przez API; koszt > wartość |
| Testy | `discover.spec.ts` selektor `.grid h3` kruchy | 🚫 wontfix — pęknie dopiero przy zmianie layoutu, wtedy naprawić przez `data-testid` |
| Testy | Orphan `test_qcount_tmp.cpython-313.pyc` | ❌ false-positive — lokalny artefakt `__pycache__` (gitignored), nie ma go w repo |
| Testy | OpenAPI snapshot wrażliwy na upgrade drf-spectacular, przypiąć wersję | ❌ false-positive — `uv.lock` przypina wersję w praktyce; CI deterministyczne |
| Testy | `settings.spec.ts` mutuje `authUser.password` (osierocone konto przy wywrotce) | 🚫 wontfix — znany TODO w kodzie, niska szkodliwość lokalna |
| Testy | Komentarz przy mocku `characters.views.generate_characters_task.delay` | 🚫 wontfix — patch w poprawnym miejscu; komentarz zbędny |
| Infra | `ALLOWED_HOSTS` w `.env.example` bez domeny prod; root user w Dockerfile'ach | ⏭ out-of-scope — checklist wdrożenia produkcyjnego (ROADMAP „Po M11–M14"), nie audytu |
| Docs | (docs-agent zgłaszał znane: M14 w ROADMAP) | ✅ ujęte w #6 |

## Notki do ROADMAP (poza fix-spec)

- Edycja `bio` z UI — kandydat „Kiedyś".
- Checklist wdrożenia prod (uzupełnić istniejący punkt): `ALLOWED_HOSTS` z domeną, non-root user w Dockerfile'ach, weryfikacja `/media/`+`/static/` po fixie #2.

## Statystyka

Faza 1: 55 zgłoszeń (backend 15, frontend 18, infra 14, docs 18*, testy 17; *część duplikatów między agentami scalono). Faza 2: 19 zgłoszeń (kontrakt 15, phantom UI 4). Po adjudykacji: **24 pozycje confirmed** (1 blocker, 15 important, 8 zgrupowanych nit), ~20 odrzuconych/wontfix, 5 false-positives, 4 intentional, 3 out-of-scope. Hipoteza fazy 2 „phantom UI" potwierdzona (2 nowe znaleziska ważne: brak feedbacku formularzy settings, niewidzialny filtr autora).
