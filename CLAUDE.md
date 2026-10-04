# CLAUDE.md

> Mapa projektu. Pełne konwencje i decyzje — w `docs/` i `docs/decisions/`.

## Co to jest

StoryShelf — **w trakcie pivotu (2026-10-03)**: z trackera czytania na prywatną wiki o książkach (format OKF v0.2) pisaną przez Agenta LLM razem z Userem. Docelowo Django 6 + DRF + Celery/Redis/OpenRouter, a frontend od zera w React + Vite SPA ([ADR-004](docs/decisions/ADR-004-wiki-okf-pages-in-postgres.md), [ADR-005](docs/decisions/ADR-005-react-vite-spa.md)).

Kod na `dev` to na razie sam szkielet backendu (`users`: auth, konto, profil; `config`: settings, Celery), 4 kontenery: db, django, celery, redis; domena trackera usunięta; `frontend/` to szkielet nowego SPA (#87). Komendy i layout niżej opisują ten obecny kod. Plan migracji: GitHub milestones.

## Mapa dokumentacji

- Słownik domeny (używaj tych pojęć: Strona, Wzmianka, Propozycja…): @CONTEXT.md
- Architektura (docelowa): @docs/ARCHITECTURE.md
- Makiety W0: `docs/mockups/project/*.dc.html`
- Roadmapa: GitHub milestones
- Decyzje (ADR): @docs/decisions/
- Aktywny etap: @docs/superpowers/specs/ + @docs/superpowers/plans/
- Konwencje stylu: egzekwowane przez `ruff check` (Python), ESLint + Prettier (frontend)
- Pułapki środowiska dev i guarda worktree: @docs/GOTCHAS.md

## Workflow (Spec-Driven Development z superpowers)

1. `/brainstorming` → spec w `docs/superpowers/specs/`
2. `/writing-plans` → plan w `docs/superpowers/plans/`
3. `/executing-plans` lub `/subagent-driven-development` → kod
4. `/requesting-code-review` → review + poprawki
5. `/finishing-a-development-branch` → PR
6. Jeśli była znacząca decyzja architektoniczna → nowy ADR w `docs/decisions/`

## Komendy

### Backend (z `backend-django/` używając `uv`)

```bash
uv run python manage.py runserver 0.0.0.0:8000
uv run python manage.py check
uv run python manage.py migrate
DJANGO_ENV=dev uv run python manage.py test                                # wszystkie testy
DJANGO_ENV=dev uv run python -m pytest                                      # testy (pytest)
uv run ruff check .                                                        # lint
uv run ruff check --fix .
```

> Testy z hosta wymagają żywej dev-DB (`make dev-up`); `make verify` ustawia `DATABASE_URL` sam.

### Docker dev stack

```bash
make dev-up          # db, django, celery, redis
make dev-down
make dev-build
make verify          # lint + testy (CI equivalent; wymaga npm ci w frontend/)
```

### Frontend (z `frontend/`, Node 24)

```bash
npm ci
npm run dev          # http://localhost:5173, proxy /api → :8000
npm run typecheck
npm run lint
npm run format       # / format:check
npm run test         # Vitest
npm run build
```

## Twarde reguły

- **`DJANGO_ENV=dev` wymagane do testów** — bez tego settings nie ładują się poprawnie.
- **Nie commituj bezpośrednio do `main`** — feature branch lub worktree.
- **Conventional commits**: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`.
- **Reset DB zamiast pisania migracji w dev**: `manage.py flush --no-input && manage.py migrate`.
- **Nie dodawaj localStorage token storage** — JWT przez HttpOnly cookies (patrz @docs/decisions/ADR-001-jwt-httponly-cookies.md).
- **Nie pomijaj `/writing-plans` po `/brainstorming`** — spec bez planu = chaos w implementacji. Wyjątek: User wprost każe wykonać prosto ze speki.

## Layout (skrót)

```
backend-django/    Django 6 + DRF; apps: users, config
frontend/          React 19 + Vite SPA; TanStack Router (src/routes/) + Query, Tailwind v4, shadcn
infra/             compose (dev/prod), caddy, scripts/ (deploy, openapi), .env(.example)
docs/              ARCHITECTURE.md, decisions/, superpowers/
.claude/           settings, agents/
```

API: `http://localhost:8000/api/` · Swagger: `/api/docs/` · Admin: `/admin/`
