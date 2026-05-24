# CLAUDE.md

> Mapa projektu. Pełne konwencje i decyzje — w `docs/` i `docs/decisions/`.

## Co to jest

StoryShelf — book-tracking + literary analysis. Django 6 REST API + SvelteKit 2 SSR, Docker Compose.
NER (spaCy en_core_web_trf, CPU-only) i LLM (OpenRouter) w workerach Celery.

## Mapa dokumentacji

- Architektura: @docs/ARCHITECTURE.md
- Roadmapa: @docs/ROADMAP.md
- Decyzje (ADR): @docs/decisions/
- Aktywny etap: @docs/superpowers/specs/ + @docs/superpowers/plans/
- Konwencje stylu: egzekwowane przez `ruff check` (Python) i `vitest` + `eslint` (Vue)

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
DJANGO_ENV=dev uv run python -m pytest analysis/tests/                     # NLP (pytest)
uv run ruff check .                                                        # lint
uv run ruff check --fix .
```

### Frontend (z `svelte-frontend/`)

```bash
npm run dev          # Vite na 5174
npm run check        # svelte-check + TypeScript
npm run lint         # ESLint + Prettier
npm run build        # adapter-node build
npm run types:api    # regeneruj typy z openapi.yml
```

### Docker dev stack

```bash
make dev-up          # db, redis, rabbitmq, django, celery-ner, celery-llm, flower, frontend
make dev-down
make dev-build
make verify          # lint + testy (CI equivalent)
```

Seed: `uv run python ../infra/scripts/seed.py` (z `backend-django/`)

## Twarde reguły

- **`DJANGO_ENV=dev` wymagane do testów** — bez tego settings nie ładują się poprawnie.
- **Nie commituj bezpośrednio do `main`** — feature branch lub worktree.
- **Conventional commits**: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`.
- **Reset DB zamiast pisania migracji w dev**: `manage.py flush --no-input && manage.py migrate`.
- **Nie dodawaj localStorage token storage** — JWT przez HttpOnly cookies (patrz @docs/decisions/ADR-001-jwt-httponly-cookies.md).
- **Nie pomijaj `/writing-plans` po `/brainstorming`** — spec bez planu = chaos w implementacji.

## Layout (skrót)

```
backend-django/    Django 6 + DRF; apps: books, library, users, shelf, reviews, analysis, config
svelte-frontend/src/  SvelteKit 2 SSR; hooks.server.ts, lib/api/, lib/config.ts, routes/
infra/             docker-compose (dev/prod), caddy, rabbitmq defs, scripts/seed.py
docs/              ARCHITECTURE.md, ROADMAP.md, decisions/, superpowers/
.claude/           settings, agents/
```

API: `http://localhost:8000/api/` · Swagger: `/api/docs/` · Flower: `:5555` · Svelte: `:5174`
