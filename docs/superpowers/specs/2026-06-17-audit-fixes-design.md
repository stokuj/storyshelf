# Audit Fixes — Design (Spec)

> Data: 2026-06-17 · Gałąź: `fix/audit-2026-06` · Źródło: audyt z 2026-06-16
> (workflow `project-audit`, 35 agentów, 29 potwierdzonych findingów: 3 high / 5 medium / 14 low / 7 info).

## Cel

Naprawić findingi z audytu w jednym batchu (jedna gałąź, jeden PR — zgodnie ze wzorcem PR #79
„holistic audit fixes, 24 findings"). Każdy finding albo dostaje realną poprawkę, albo
**świadomą decyzję „won't-fix" z uzasadnieniem** (gdy sam audyt oznaczył go jako
„acceptable / no change needed / confirm intentional").

### Kryteria sukcesu

- Wszystkie findingi „actionable" naprawione, z testem reprodukującym tam, gdzie to ma sens (TDD).
- `make verify` zielone (lint + testy backend), `npm run check`/`lint` zielone, E2E przechodzą.
- Findingi „won't-fix" jawnie udokumentowane (tu w spec + tam, gdzie warto, 1-liniowy komentarz w kodzie).
- Brak zmian wykraczających poza listę findingów (rule #3: chirurgiczne zmiany).

## Decyzja: findingi „no-change" (6)

Audyt sam oznaczył je jako niewymagające zmiany kodu. Default = **won't-fix + uzasadnienie**,
z wyjątkami gdzie tani, zerowy-ryzyko komentarz/zmiana podnosi czytelność.

| Finding | Decyzja | Uzasadnienie |
|---------|---------|--------------|
| `ratings/signals.py:9-21` (lock + re-aggregate) | **won't-fix** | Poprawne; hotspot dopiero przy skali, której projekt nie ma (single-tenant, <10k książek). Inkrementalne liczniki = over-engineering. |
| `reviews/views.py:91-100` (extra COUNT na lajk) | **won't-fix** | Jeden COUNT na toggle, nieszkodliwy. Zmiana = kosmetyka bez wartości. |
| `users/views.py:188-218` (email → brak reissue JWT) | **comment-only** | Funkcjonalnie OK (JWT na user.id, nie email). Dodać 1-liniowy komentarz, że asymetria vs zmiana hasła jest świadoma. |
| `infra/.env` (lokalny, gitignored) | **won't-fix** | Brak czego naprawiać — plik poprawnie nieśledzony. Świadomość tylko. |
| `.github/workflows/ci.yml` (brak deploy-step) | **won't-fix** | Deploy celowo odłożony (ROADMAP, decyzja usera). Poza zakresem tego batcha. |
| `svelte-frontend/playwright.config.ts:24-28` (E2E na Vite, nie prod build) | **won't-fix** | „Acceptable for MVP". Smoke E2E na buildzie prod = osobny, większy temat. |

> Pozostałe 23 findingi → realne poprawki, pogrupowane niżej.

## Grupy robocze

Kolejność = ryzyko/wartość malejąco. Każda grupa to spójny obszar (ułatwia review i ewentualny rollback).

### A. Prod deployment hardening (config) — 2× high, 2× low

- **A1 (high)** `infra/compose/docker-compose.prod.yml:76-89` — serwis `caddy` nie dostaje
  `DOMAIN`/`CADDY_ACME_EMAIL`. Dodać `env_file: - ../.env` (jak django/celery/svelte).
- **A2 (high)** `infra/.env.example:13` + `config/settings/prod.py` — prod dziedziczy
  `ALLOWED_HOSTS=localhost,127.0.0.1`, `DOMAIN` nie jest wpinany → 400 DisallowedHost.
  Fix: `prod.py` dokleja `os.getenv("DOMAIN")` do `ALLOWED_HOSTS` (jeśli ustawiony) **oraz**
  poprawka komentarza/instrukcji w `.env.example` (że prod musi mieć domenę).
- **A3 (low)** `backend-django/Dockerfile` + `svelte-frontend/Dockerfile.prod` — dodać non-root
  user (`useradd`/`adduser` + `USER`). Znany TODO z ROADMAP.
- **A4 (low)** `infra/caddy/Caddyfile` + `backend-django/config/urls.py:37-43` — serwować
  `/media` i `/static` w prod przez Caddy `file_server` z wolumenu zamiast proxować do Django.
  *(Niższy priorytet — jeśli okaże się ryzykowne dla wolumenów, zostaje jako follow-up.)*

### B. Frontend auth / SSR refresh — 1× medium, 2× low (NAJWYŻSZE RYZYKO)

Dotyka ADR-001 (JWT HttpOnly cookies) i ADR-002 (same-origin `/api`). Implementacja musi je zachować.

- **B1 (medium)** `svelte-frontend/src/lib/api/_client.ts:44-91` — SSR 401-refresh gubi rotację:
  `attemptTokenRefresh` zwraca tylko `res.ok`, a retry idzie przez `event.fetch`→`handleFetch`
  ze starym cookie; przeglądarka nigdy nie dostaje zrotowanego tokenu.
- **B2 (low)** `routes/books/[slug]/+page.server.ts:13-28` — 7 równoległych auth-fetchy →
  przy wygasłym tokenie burst 7× `/auth/refresh/`; rotacja blacklistuje pozostałe.
- **B3 (low)** `routes/settings/+page.server.ts:57-95` — akcja zmiany hasła gubi Set-Cookie
  (backend blacklistuje stare tokeny + wydaje nowe) → user wylogowany przy następnym refresh.

**Kierunek (do doprecyzowania w planie):** scentralizować SSR-refresh w jednym miejscu
per-request (hook / współdzielony SSR-wrapper), które: (a) odświeża **raz** i dedupuje
równoległe 401, (b) przechwytuje Set-Cookie z odpowiedzi refresh i forwarduje do przeglądarki
przez `cookies.set()`, (c) używa świeżego tokenu na retry. Rozwiązuje B1+B2 łącznie.
B3: dodać `forwardSetCookies(res, cookies)` w akcji hasła (jak login/signup).
**To jedyny obszar, gdzie dopuszczam descope/split**, jeśli okaże się zbyt inwazyjny dla auth —
wtedy minimalny fix (forward rotacji do przeglądarki) + reszta jako follow-up.

### C. Frontend correctness + a11y — 1× high, 3× low

- **C1 (high)** `routes/discover/+page.svelte:19-46` — navbar search no-opuje na `/discover`
  (stan z jednorazowego snapshotu `data`, brak re-sync). Fix: `$effect`/re-seed na zmianę
  `data.initialQ`/`initialBooks` przy nawigacji na tej samej trasie.
- **C2 (low)** `routes/settings/data/export/+server.ts:7-11` — GET-handler odpala side-effecting
  POST. Fix: wyzwalać export przez POST (form action / fetch), nie GET-link.
- **C3 (low)** `lib/components/discover/FilterBar.svelte:64` + `routes/users/+page.svelte:79-85`
  — search-inputy bez `aria-label`. Dodać.
- **C4 (low)** `lib/components/discover/FilterBar.svelte:82-104` — `role="listbox"` z dziećmi
  `<button>` bez `role=option`/`aria-selected`, bez nawigacji strzałkami. Fix: albo poprawne
  role+klawiatura, albo zdjąć `listbox` i traktować jak menu buttonów (preferowane — prostsze).

### D. Backend — 2× low, 2× info

- **D1 (low)** `config/settings/base.py:104-114` — `auth_register` default `100/hour` (vs login
  `10/min`). Obniżyć do `~10/hour` lub `20/day`; zostawić override przez env.
- **D2 (low)** `feed/views.py:110-151` — kursor gubi grupę >21 itemów o równym timestampie.
  Fix: stabilny wtórny klucz sortowania/kursora (np. `id`) albo dobranie itemów przy nasyconej
  granicy. (Spójne z istniejącą logiką „tie-swallowing".)
- **D3 (info)** `users/serializers.py:191-206` — allowlist MIME po spoofowalnym `content_type`.
  Fix: walidować po `PIL img.format` zamiast po `file.content_type`.
- **D4 (info)** `characters/services.py:57-65` — dedup relacji po `id(obj)` zamiast `.pk`.
  Fix: klucz `(source.pk, target.pk, relation_type)` — zgodny z DB constraint.

### E. Testy + CI — 3× medium, 1× low, (1× info)

- **E1 (medium)** `.github/workflows/ci.yml:42-55` — dodać kroki `manage.py check` oraz
  `makemigrations --check --dry-run` (lustro `make verify`).
- **E2 (medium)** brak testów throttli — dodać testy z `override_settings` re-enable +
  asercja 429 dla `auth_register` i `character_generate` (cost-control LLM).
- **E3 (medium)** brak E2E postaci (M13/M14) — `characters.spec.ts`: seed CharacterAnalysis
  (DONE) + Characters przez API, asercja render kart/detalu/relacji. Bez live-LLM.
- **E4 (info)** `.github/workflows/ci.yml:49-55` — test OpenAPI snapshot leci 2× (pytest +
  osobny `manage.py test`). Usunąć redundantny krok `manage.py test` (pytest go pokrywa).
- **E6 (low)** `svelte-frontend/e2e/discover.spec.ts:21-28` — asercje na dokładny globalny
  licznik książek. Zmienić na asercje obecności/względne (odporne na seed-pollution).
- **E5 (low)** `svelte-frontend/package.json` — `"test": "vitest run"` to martwy skrypt (zero
  `*.test.ts`, brak bloku `test` w `vite.config.ts`, nie w CI). **Decyzja: usunąć** martwy
  skrypt + nieużywane devDeps (`vitest`, `@vitest/ui`, `jsdom`) — YAGNI. (Alternatywa: dopisać
  config + testy — odrzucona jako busywork pod martwy skrypt.)

### F. Docs — 1× medium, 1× low

- **F1 (medium)** `docs/decisions/ADR-002-...:21` — ADR mówi `handle_path /api/*` (strip → 404),
  realnie `handle /api/*`. Poprawić ADR na zgodny z Caddyfile.
- **F2 (low)** `docs/ARCHITECTURE.md` — diagram wiesza `Character`/`CharacterRelation` pod
  `CharacterAnalysis`, a oba FK do `Book`. Przerysować: `Book` posiada Character/Relation,
  `CharacterAnalysis` to sibling OneToOne(Book) ze statusem.

## Strategia testów (TDD gdzie sensowne)

- **Backend** (`DJANGO_ENV=dev`): D1 (429 po przekroczeniu), D2 (tie-group nie gubi itemów),
  D3 (odrzucenie podmienionego content_type, akceptacja realnego JPEG/PNG/WebP),
  D4 (dedup relacji po pk), E2 (throttle 429). A2 — test, że prod ALLOWED_HOSTS zawiera DOMAIN.
- **Frontend**: C1, C2 — E2E (Playwright). C3/C4 — `npm run check`/lint + asercja a11y w E2E
  gdzie tanio. E3 — nowy `characters.spec.ts`. E6 — przepisać asercje.
- **B (auth/SSR)** — najtrudniejsze do testu; minimalnie E2E „login → wygasły access →
  poprawny silent refresh na SSR-loadzie" + asercja, że kolejny load nie robi ponownego refresh.

## Poza zakresem (świadomie)

- Wdrożenie produkcyjne / automatyzacja deploy (ROADMAP — osobna decyzja usera).
- Smoke E2E na produkcyjnym buildzie adapter-node (finding playwright — won't-fix MVP).
- Refaktory niezwiązane z findingami.

## Ryzyka

- **B (auth/SSR)** — dotyka cookies/JWT; błąd = realne wylogowania lub luka. Najostrożniejszy
  obszar, osobny commit, dedykowany review. Dopuszczalny descope.
- **A4 (media/static przez Caddy)** — zmiana ścieżki serwowania; jeśli wolumeny nie pasują,
  zostaje follow-up zamiast forsować.
- **A2 (ALLOWED_HOSTS)** — zmiana w `prod.py`; nie może zepsuć dev/test (gdzie DOMAIN pusty).

## Plan commitów (konwencja repo)

1. Commit: dodanie tej specki (+ planu, gdy powstanie).
2. Implementacja — konwencjonalne commity per grupa (A–F).
3. Przed PR: usunięcie specki/planu (osobny commit).
4. Po zatwierdzonym pushu/review: ewentualny squash wg ustaleń.
