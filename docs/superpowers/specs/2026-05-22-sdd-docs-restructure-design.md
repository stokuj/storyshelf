# SDD docs restructure — design

> **Status:** Spec — czeka na akceptację, potem `/writing-plans`.
> **Data:** 2026-05-22
> **Autor sesji:** brainstorming z Claude (Opus 4.7)

## 1. Cel

Reorganizacja dokumentacji StoryShelf pod model **Spec-Driven Development** z trzema warstwami:

| Warstwa | Orientacja | Cykl życia |
|---------|-----------|------------|
| `docs/superpowers/specs/` + `plans/` | **przyszłość** (co budujemy) | Aktywna przed/podczas implementacji |
| `docs/` (architecture, ADR, ROADMAP) | **ponadczasowo** (stabilna referencja) | Zmienia się rzadko, świadomie |
| `wiki/` | **teraźniejszość** (stan systemu) | Żywa, aktualizowana co PR |

Cele wymierne:
- `CLAUDE.md` ≤ 100 linii, rola: mapa + komendy + twarde reguły
- Wyeliminować duplikację CLAUDE.md ↔ AGENTS.md
- Wprowadzić **3 ADR-y** retrospektywne dokumentujące już podjęte decyzje
- Wprowadzić **5 seed pages** w `wiki/` pokrywających kluczowe komponenty
- Dodać **3 slash commands** (`/wiki-lint` pełny, `/wiki-query` + `/wiki-ingest` szkielety)
- Wykorzystać plugin **superpowers** do cyklu `/brainstorming` → `/writing-plans` → `/executing-plans` → `/requesting-code-review` → `/finishing-a-development-branch`

## 2. Decyzje wstępne (z brainstormingu)

| # | Pytanie | Wybór | Komentarz |
|---|---------|-------|-----------|
| 1 | Zakres iteracji | **Pełna struktura naraz** | Faza 1-4 z dokumentu SDD w jednym branchu |
| 2 | CLAUDE.md vs AGENTS.md | **AGENTS.md jako alias (2-3 linie)** | Jedno źródło prawdy w CLAUDE.md |
| 3 | Język | **Polski wszędzie** (nowe dokumenty) | README po angielsku zostaje |
| 4 | Archiwum starych planów | **Usunąć, zostawić tylko ADR-y** | Najważniejsze decyzje wyciągnięte do `docs/decisions/` |
| 5 | Strony wiki | 5: `nlp-pipeline`, `auth-flow`, `api-conventions`, `celery-workers`, `dev-setup` | Pokrywa największe skupiska gotchas |
| 6 | Retro ADR-y | 3: JWT cookies, 2 workery Celery, encje per-book (bez Chapter) | Świeże decyzje, kontekst jeszcze pamiętany |
| 7 | Podejście migracji | **B — warstwowy** (5 commitów na jednym branchu) | Bezpieczne reverty, każdy commit mergeable |
| 8 | `docs/conventions.md` + `deployment.md` | **Skreślone** | Ruff/eslint egzekwują konwencje; deployment żyje w `infra/` + README |
| 9 | `wiki/_meta/log.md` | **Tak, dla lint + ingest** | Audyt dryfu za darmo |
| 10 | Lint | **Tekstowa instrukcja w slash command**, nie skrypt Python | Spójne z modelem usera z `~/Dokumenty/LLM-WIKI/` |
| 11 | `/specify`, `/plan`, `/tasks` | **Skreślone** — superpowers to robi natywnie | Mniej kodu do utrzymania |
| 12 | Cykl SDD | review **przed** wiki update | Wiki dokumentuje stan wchodzący do merge |

## 3. Docelowa struktura katalogów

```
storyshelf/
├── CLAUDE.md                       # ~100 linii: mapa + komendy + twarde reguły
├── AGENTS.md                       # 2-3 linie: alias → CLAUDE.md
├── README.md                       # bez zmian (po angielsku)
│
├── docs/
│   ├── ARCHITECTURE.md             # ← migracja z ARCHITECTURE.md
│   ├── ROADMAP.md                  # NOWY: backlog + etapy + non-goals
│   ├── decisions/
│   │   ├── ADR-001-jwt-httponly-cookies.md
│   │   ├── ADR-002-dwa-workery-celery.md
│   │   └── ADR-003-encje-ner-per-book.md
│   └── superpowers/                # używany przez plugin superpowers
│       ├── specs/                  # tworzone przez /brainstorming
│       └── plans/                  # tworzone przez /writing-plans
│
├── docs/llm-wiki/                           # żywa baza wiedzy o stanie systemu
│   ├── _meta/
│   │   ├── INDEX.md                # format llms.txt
│   │   └── log.md                  # append-only dziennik operacji
│   ├── auth-flow.md
│   ├── nlp-pipeline.md
│   ├── api-conventions.md
│   ├── celery-workers.md
│   └── dev-setup.md
│
├── .claude/
│   ├── settings.json               # bez zmian
│   ├── settings.local.json         # bez zmian
│   ├── commands/
│   │   ├── wiki-lint.md            # PEŁNY (6 reguł, tekstowo)
│   │   ├── wiki-query.md           # szkielet z TODO
│   │   └── wiki-ingest.md          # szkielet z TODO
│   └── agents/
│       └── README.md               # placeholder: jak dodawać subagentów
```

## 4. Mapowanie plików

| Akcja | Źródło | Cel |
|-------|--------|-----|
| Move | `ARCHITECTURE.md` | `docs/ARCHITECTURE.md` |
| Shrink | `CLAUDE.md` (138 linii) | `CLAUDE.md` (~100 linii — mapa) |
| Shrink | `AGENTS.md` (243 linie) | `AGENTS.md` (2-3 linie aliasu) |
| Distribute (gotchas) | `AGENTS.md` → sekcja "Gotchas" | 5 stron `docs/llm-wiki/` (mapa poniżej) |
| Distribute (conventions) | `AGENTS.md` → sekcja "Conventions" | `docs/llm-wiki/api-conventions.md` + ruff/eslint |
| New | — | `docs/ROADMAP.md` |
| New | — | `docs/decisions/ADR-{001,002,003}-*.md` |
| New | — | `docs/llm-wiki/{auth-flow,nlp-pipeline,api-conventions,celery-workers,dev-setup}.md` |
| New | — | `docs/llm-wiki/_meta/{INDEX,log}.md` |
| New | — | `.claude/commands/{wiki-lint,wiki-query,wiki-ingest}.md` |
| New | — | `.claude/agents/README.md` |
| Bez zmian | `README.md`, `Makefile`, kod, `infra/`, `.claude/settings*.json` | — |

### Mapa gotchas AGENTS.md → docs/llm-wiki/

| Gotcha | Trafia do |
|--------|-----------|
| `Serie` (singular), `analyse_book` not idempotent, `NER_MIN_OCCURRENCES`, no Chapter, entity models per-book, spaCy Python pin | `docs/llm-wiki/nlp-pipeline.md` |
| JWT HttpOnly cookies, auth init w router.beforeEach, refresh flow, Swagger fallback | `docs/llm-wiki/auth-flow.md` |
| Trailing slashes, camelCase mapping, no pagination, `avg_rating` vs `rating`, `relation_type`, `useAsyncState` timeout | `docs/llm-wiki/api-conventions.md` |
| RabbitMQ pin, definitions.json vhosts, DLX, Flower, celery-ner vs celery-llm pools, `CELERY_TASK_ROUTES`, `CELERY_TASK_ALWAYS_EAGER` w dev | `docs/llm-wiki/celery-workers.md` |
| `DJANGO_ENV=dev`, seed.py, Docker volume vs .venv, Alpine healthcheck IPv6, frontend rebuild, Caddy HTTPS, nginx location priority, root `.dockerignore`, reset DB | `docs/llm-wiki/dev-setup.md` |

## 5. Treść CLAUDE.md (~100 linii)

```markdown
# CLAUDE.md

> Mapa projektu. Pełne konwencje, gotchas i decyzje — w `docs/`, `docs/llm-wiki/`, `docs/decisions/`.

## Co to jest
StoryShelf — book-tracking + literary analysis. Django 6 REST API + Vue 3 SPA, Docker Compose.
NER (spaCy en_core_web_trf, CPU-only) i LLM (OpenRouter) w workerach Celery.

## Mapa dokumentacji
- Architektura: @docs/ARCHITECTURE.md
- Roadmapa: @docs/ROADMAP.md
- Decyzje (ADR): @docs/decisions/
- Aktywny etap: @docs/superpowers/specs/ + @docs/superpowers/plans/
- Stan systemu (żywa wiedza): @docs/llm-wiki/_meta/INDEX.md
- Konwencje stylu: egzekwowane przez `ruff check` (Python) i `vitest` + `eslint` (Vue)

## Workflow (Spec-Driven Development z superpowers)
1. `/brainstorming` → spec w `docs/superpowers/specs/`
2. `/writing-plans` → plan w `docs/superpowers/plans/`
3. `/executing-plans` lub `/subagent-driven-development` → kod
4. `/requesting-code-review` → review + poprawki
5. `/wiki-ingest` → propozycja zmian w `docs/llm-wiki/` (tylko po review)
6. `/wiki-lint` → spójność `docs/llm-wiki/`
7. `/finishing-a-development-branch` → PR
8. Jeśli była znacząca decyzja architektoniczna → nowy ADR w `docs/decisions/`

## Reguła dla pytań o istniejący kod
Zanim odpowiesz: sprawdź `docs/llm-wiki/_meta/INDEX.md`, potem właściwą stronę.
Nie wnioskuj z samego kodu, jeśli wiki istnieje. Jeśli wiki kłamie — popraw ją.

## Komendy

### Backend (z `backend-django/` używając `uv`)
\`\`\`bash
uv run python manage.py runserver 0.0.0.0:8000
uv run python manage.py check
uv run python manage.py migrate
DJANGO_ENV=dev uv run python manage.py test
DJANGO_ENV=dev uv run python -m pytest analysis/tests/
uv run ruff check .
\`\`\`

### Frontend (z `frontend/`)
\`\`\`bash
npm run dev          # Vite na 5173
npm test             # Vitest jsdom
npm run build
\`\`\`

### Docker dev stack
\`\`\`bash
make dev-up
make dev-down
make verify          # lint + testy (CI equivalent)
\`\`\`

Seed: `uv run python ../infra/scripts/seed.py` (z `backend-django/`)

## Twarde reguły
- **`DJANGO_ENV=dev` wymagane do testów** — bez tego settings nie ładują się poprawnie.
- **Nie commituj bezpośrednio do `main`** — feature branch lub worktree.
- **Conventional commits**: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`.
- **Reset DB zamiast pisania migracji w dev**: `manage.py flush --no-input && manage.py migrate`.
- **Nie dodawaj localStorage token storage** — JWT przez HttpOnly cookies (patrz @docs/decisions/ADR-001).
- **Nie pomijaj writing-plans po brainstorming** — spec bez planu = chaos w implementacji.
- **Wiki update PRZED PR, nie po** — `/wiki-ingest` jako część tej samej gałęzi co kod.

## Layout (skrót)
\`\`\`
backend-django/    Django 6 + DRF; apps: books, library, users, shelf, reviews, analysis, config
frontend/src/      Vue 3 SPA; api.js, auth.js, router.js, views/, components/, composables/
infra/             docker-compose (dev/prod), caddy, rabbitmq defs, scripts/seed.py
docs/              ARCHITECTURE.md, ROADMAP.md, decisions/, llm-wiki/, superpowers/
docs/llm-wiki/     żywa wiedza o stanie systemu; INDEX.md w formacie llms.txt
.claude/           settings, commands/ (wiki-lint, wiki-query, wiki-ingest), agents/
\`\`\`

API: `http://localhost:8000/api/` · Swagger: `/api/docs/` · Flower: `:5555` · Frontend: `:5173`
```

## 6. ADR-y (3 retrospektywne)

Format: Michael Nygard (Kontekst → Opcje → Decyzja → Konsekwencje → Linki).
Status: `Proponowane` / `Zaakceptowane` / `Wycofane` / `Superseded by ADR-XXX`. Immutable.

### ADR-001 — JWT przez HttpOnly cookies (zamiast localStorage)
- **Kontekst:** XSS-vulnerability localStorage, frontend audit 2026-05-14
- **Opcje:** localStorage / sessionStorage / HttpOnly cookies / memory-only singleton
- **Decyzja:** HttpOnly cookies + SameSite=Lax, refresh w osobnym cookie z `path=/api/users/token/refresh/`, Bearer header jako fallback dla Swagger
- **Konsekwencje:** `credentials: 'include'` na każdym fetchu, silent refresh transparentny, twarda reguła "no localStorage token storage"
- **Linki:** commits 992ce90, 2b32ff3, 0432ef2, 9028719, 429e1a7; `users/cookie_auth.py`, `frontend/src/api.js`; [[auth-flow]]

### ADR-002 — Dwa osobne workery Celery (prefork NER + gevent LLM)
- **Kontekst:** NER CPU-bound (spaCy), LLM I/O-bound (OpenRouter) — jeden pool nie pasuje do obu
- **Opcje:** jeden prefork / jeden gevent / dwa workery / asyncio (niemożliwe dla spaCy)
- **Decyzja:** `celery-ner --pool prefork` (queue `ner`), `celery-llm --pool gevent` (queue `llm`), routing przez `CELERY_TASK_ROUTES`, DLX dla failed tasks
- **Konsekwencje:** 2 kontenery Docker, Flower widzi oba pool typy, RabbitMQ pin do `3-management-alpine` (v4 łamie Celery 5.6), `definitions.json` z `vhosts` przed kolejkami
- **Linki:** `config/celery.py`, `infra/compose/docker-compose.dev.yml`, `infra/rabbitmq/definitions.json`; [[celery-workers]], [[nlp-pipeline]]

### ADR-003 — Encje NER per-book, brak modelu Chapter
- **Kontekst:** Pierwotny schemat (Chapter + global entities) miał kolizje nazw między książkami i pipeline z 5 tasków z race condition
- **Opcje:** Chapter+global / Chapter+per-book / **bez Chapter, per-book** / bez Chapter, global+M2M
- **Decyzja:** Usunięcie modelu `Chapter`, `Book.text` jako tymczasowy storage (czyszczony po analizie), `unique_together("name", "book")` na `BookCharacter`/`BookPlace`/`BookOrganization`, `CharacterRelationship` z `book` FK
- **Konsekwencje:** `analyse_book` nie jest idempotentny (re-upload akumuluje — manual cleanup wymagany), brak cross-book query "wszystkie książki z Frodo" (na razie), BookDetail response bez `chapters`
- **Linki:** `analysis/models.py`, `analysis/tasks.py`; [[nlp-pipeline]]; supersedes wcześniejszy design

## 7. Strony wiki — format i seed

### Wymagany frontmatter

```yaml
---
title: <Tytuł>
last_updated: YYYY-MM-DD
last_verified_commit: <git-sha>
owns:
  - <path/to/file>
depends_on: [<external systems>]
related_pages: [<slug>, ...]
status: stable | wip | deprecated
---
```

`last_verified_commit` porównywane przez `/wiki-lint` z `git log -1 --format=%H -- <owns>`.

### Wymagane sekcje (każda strona, poza `status: wip`)

1. **Co to jest** — 2-3 zdania, jednoznacznie
2. **Jak działa** — flow, sekwencja, mechanizmy
3. **Decyzje** — linki do ADR (nie powtarzamy treści)
4. **Typowe operacje** — przykłady kodu/komend
5. **Pułapki** — gotchas
6. **Pytania, na które ta strona odpowiada** — działa jak embedding-for-the-poor

### 5 seed pages — zakres

| Strona | `owns:` | Główne treści |
|--------|---------|---------------|
| `auth-flow.md` | `users/cookie_auth.py`, `users/views.py`, `users/serializers.py`, `frontend/src/auth.js`, `frontend/src/api.js` | JWT cookies, silent refresh, `authState` singleton, router init, gotchas (no localStorage, credentials: include, CSRF, Swagger fallback). Linki: ADR-001. |
| `nlp-pipeline.md` | `analysis/tasks.py`, `analysis/ner_engine.py`, `analysis/llm_engine.py`, `analysis/models.py` | Trigger admin → `analyse_book` → chunking 400/50 → spaCy → encje per-book → `relations_for_book` → LLM. Gotchas: `NER_MIN_OCCURRENCES=5`, brak idempotencji, czyszczenie `Book.text`, OpenRouter try/except przy imporcie. Linki: ADR-002, ADR-003. |
| `api-conventions.md` | `*/serializers.py`, `*/urls.py`, `frontend/src/api.js`, `frontend/src/composables/useAsyncState.js` | Trailing slashes, camelCase mapping (`source="snake"`), `pagination_class = None`, `avg_rating` vs `rating`, `relation_type`, `useAsyncState` timeout 15s, AlertMessage convention. |
| `celery-workers.md` | `config/celery.py`, `infra/compose/docker-compose.dev.yml`, `infra/rabbitmq/definitions.json` | Dwa pool types, routing przez kolejki, RabbitMQ pin + DLX + vhosts, Flower :5555, `CELERY_TASK_ALWAYS_EAGER` w dev. Linki: ADR-002, [[nlp-pipeline]]. |
| `dev-setup.md` | `Makefile`, `infra/compose/*`, `backend-django/pyproject.toml`, `infra/scripts/seed.py` | Pierwsze uruchomienie, `make dev-up`, `DJANGO_ENV=dev`, reset DB zamiast migracji, seed, Alpine IPv6 healthcheck, frontend rebuild flow, spaCy Python pin (>=3.13,<3.14). |

### `docs/llm-wiki/_meta/INDEX.md` (format llms.txt)

```markdown
# StoryShelf — llm-wiki

> Żywa baza wiedzy o stanie systemu StoryShelf. SDD z superpowers.
> Architektura: @../../ARCHITECTURE.md

## Komponenty
- [Auth Flow](../auth-flow.md): JWT przez HttpOnly cookies, refresh, integracja Django + Vue
- [NLP Pipeline](../nlp-pipeline.md): spaCy NER + LLM, 2 taski Celery, encje per-book
- [API Conventions](../api-conventions.md): kontrakt frontend↔backend
- [Celery Workers](../celery-workers.md): NER (prefork) + LLM (gevent), RabbitMQ, DLX
- [Dev Setup](../dev-setup.md): Docker Compose, DJANGO_ENV, reset DB, seed, healthchecks

## Architektura
- [System overview](../../ARCHITECTURE.md)
- [Decyzje (ADR)](../../decisions/)
- [Roadmapa](../../ROADMAP.md)

## Meta
- [Log operacji wiki](log.md)
```

### `docs/llm-wiki/_meta/log.md` (append-only)

```markdown
# Log operacji wiki

Format: `## [YYYY-MM-DD HH:MM] <komenda> | <wynik 1-linijka>`

## [2026-05-22 14:30] init | utworzono 5 stron seed + INDEX
```

## 8. Komendy `.claude/commands/`

### `wiki-lint.md` (PEŁNY)

Workflow tekstowy — Claude wykonuje ręcznie 6 reguł:

**R1.** Pliki w `owns:` istnieją w repo.
**R2.** `related_pages:` istnieją i back-reference obustronna.
**R3.** `last_verified_commit` nie starszy niż HEAD plików w `owns:` (przez `git log -1 --format=%H -- <paths>`). Wyjątek: `status: wip`.
**R4.** Strony-sieroty (nieosiągalne z `INDEX.md`).
**R5.** Wymagane sekcje obecne (Co to jest / Jak działa / Pułapki / Pytania).
**R6.** Linki `[[slug]]` i markdown linki działają.

Po raporcie: dopisz wpis do `docs/llm-wiki/_meta/log.md`. Tryby: pełny / `<slug>` / `--fix`.

### `wiki-query.md` (SZKIELET)

Cel: odpowiadać na pytania o system z wiki. Procedura: INDEX → match po sekcji "Pytania" → czytanie 1-3 stron → odpowiedź z cytatami `[[slug]]#sekcja`. **TODO**: implementacja gdy wiki ≥10 stron lub gdy ręczne czytanie wejdzie w nawyk.

### `wiki-ingest.md` (SZKIELET)

Cel: po code review zaproponować zmiany w wiki na podstawie diffu. **Pre-merge requirement**, nie post-merge hook. Procedura: `git diff main...HEAD` → match plików do `owns:` → diff propozycji → aktualizacja `last_verified_commit` → log. **TODO**: implementacja gdy będzie 3-5 PR-ów ręcznie zaktualizowanych.

### `.claude/agents/README.md` (PLACEHOLDER)

Pusty katalog, README z formatem subagenta. Kandydaci listed (`django-reviewer`, `vue-reviewer`, `celery-task-writer`, `wiki-page-author`) — nie tworzymy teraz.

## 9. `docs/ROADMAP.md`

Sekcje: **Zrobione** (tabela z linkami do ADR) | **W toku** | **Następne** (priorytetyzowane: produkcja, idempotentność `analyse_book`, disambiguation aliasów, search/filter) | **Kiedyś** (bez priorytetu: rekomendacje, mobile, social) | **Czego NIE robimy** (immutable jak ADR: skala >10k książek, real-time collab, native mobile, fine-tuning LLM, full-text search, płatności).

Ręcznie utrzymywany, ~50-80 linii.

## 10. Plan commitów (podejście B, warstwowy)

Branch: `refactor/sdd-docs-restructure`. **5 logicznych commitów**:

| # | Commit | Zawartość |
|---|--------|-----------|
| 1 | `docs: extract architecture, add ROADMAP, slim AGENTS` | `git mv ARCHITECTURE.md docs/ARCHITECTURE.md`, nowy `docs/ROADMAP.md`, edycja `AGENTS.md` (alias), `.gitkeep` w `docs/superpowers/{plans,specs}/` |
| 2 | `docs: add 3 ADRs for foundational decisions` | 3 pliki w `docs/decisions/` |
| 3 | `docs(llm-wiki): seed pages — auth, nlp, api, celery, dev-setup` | 5 stron w `docs/llm-wiki/` + `_meta/{INDEX,log}.md`, gotchas dystrybuowane z AGENTS.md |
| 4 | `feat(claude): wiki-lint + wiki-query/ingest skeletons` | 3 komendy + `agents/README.md` |
| 5 | `docs(claude): shrink CLAUDE.md to ~100 lines as map` | Przepisanie CLAUDE.md jako mapa |

**Każdy commit przejdzie `make verify` zielony.** Reverty proste — cofnięcie commita 5 zostawia działający projekt z poprzednim CLAUDE.md.

PR-merge: jeden PR z 5 commitami. Po merge — branch usunięty.

## 11. Verification (po implementacji)

- [ ] `wc -l CLAUDE.md` < 105
- [ ] `AGENTS.md` < 10 linii (alias)
- [ ] `ls docs/decisions/ADR-*.md | wc -l` == 3
- [ ] `ls docs/llm-wiki/*.md | wc -l` == 5 (bez `_meta/`)
- [ ] `ls docs/llm-wiki/_meta/{INDEX,log}.md` istnieją
- [ ] `ls .claude/commands/wiki-*.md | wc -l` == 3
- [ ] Brak `ARCHITECTURE.md` w root (przeniesione do `docs/ARCHITECTURE.md`)
- [ ] `make verify` zielony
- [ ] `git log --oneline | head -5` pokazuje 5 commitów w kolejności z sekcji 10

## 12. Non-goals tej iteracji

- Implementacja `/wiki-query` i `/wiki-ingest` — pozostają szkieletami z TODO
- Subagenci (`.claude/agents/*.md` poza README) — brak konkretnych
- Migracja istniejących planów `docs/superpowers/plans/` jako archiwum — decyzja: usuwamy
- Pełnotekstowe wyszukiwanie w wiki (np. RAG z embeddings) — premature
- Hook'i git (pre-commit lint wiki) — premature, lint ręcznie póki nie powstanie nawyk
