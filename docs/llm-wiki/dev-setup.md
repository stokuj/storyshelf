---
title: Dev Setup
last_updated: 2026-05-22
last_verified_commit: 86ea9b0
owns:
  - Makefile
  - infra/compose/docker-compose.dev.yml
  - backend-django/pyproject.toml
  - frontend/package.json
  - infra/scripts/seed.py
  - .env.example
depends_on:
  - Docker + Docker Compose
  - uv (Python package manager)
  - Node.js + npm
related_pages: [celery-workers, api-conventions, auth-flow, nlp-pipeline]
status: stable
---

## Co to jest

Wszystko, co potrzebne do pierwszego uruchomienia projektu lokalnie: zależności, kontenery,
seed danych, healthchecki, znane pułapki środowiskowe (Alpine IPv6, frontend rebuild, spaCy
Python pin).

## Jak działa

```
1. Clone repo
2. cp .env.example .env   # ustaw OPENROUTER_API_KEY (lub dummy w dev)
3. make dev-up            # docker compose up -d
4. make dev-superuser     # tworzy admin Django
5. cd backend-django && uv run python ../infra/scripts/seed.py   # 20 książek
6. Open http://localhost:5173 (Vite) lub http://localhost:8000/admin/ (Django)
```

Stack w `make dev-up`:
- `db` — PostgreSQL 16 (port 5432)
- `redis` — Celery result backend (6379)
- `rabbitmq` — broker (5672) + management UI (15672)
- `django` — REST API (8000) + Swagger (`/api/docs/`)
- `celery-ner` — NER worker (prefork)
- `celery-llm` — LLM worker (gevent)
- `flower` — Celery monitoring (5555)
- `frontend` — Vite dev server (5173)

`DJANGO_ENV=dev` aktywuje: `DEBUG=True`, `CELERY_TASK_ALWAYS_EAGER=True`, `CORS_ALLOW_ALL_ORIGINS=True`,
`CSRF_TRUSTED_ORIGINS=["http://localhost:5173"]`.

## Decyzje

- **uv zamiast pip/poetry**: szybszy resolver, lock file (`uv.lock`), wbudowany venv
- **Reset DB zamiast migracji w dev**: szybciej iterować nad modelami, mniej śmieci w `migrations/`
- **Healthcheck z 127.0.0.1 zamiast localhost**: Alpine `wget` resolves localhost do `::1`,
  Vite słucha tylko IPv4

## Typowe operacje

**Pierwsze uruchomienie:**
```bash
git clone <repo>
cd storyshelf
cp .env.example .env
# Edytuj .env — OPENROUTER_API_KEY (dla NLP) lub dummy ('sk-dummy-api-key')
make dev-up
make dev-superuser
cd backend-django && uv run python ../infra/scripts/seed.py
```

**Codzienna praca:**
```bash
make dev-up                      # start stack
make dev-down                    # stop
make dev-build                   # rebuild images (po zmianie Dockerfile)
make verify                      # lint + tests (lokalny CI)
```

**Reset bazy danych (zamiast pisania migracji):**
```bash
cd backend-django
DJANGO_ENV=dev uv run python manage.py flush --no-input
DJANGO_ENV=dev uv run python manage.py migrate
uv run python ../infra/scripts/seed.py
```

**Testy:**
```bash
cd backend-django
DJANGO_ENV=dev uv run python manage.py test                  # wszystkie testy Django
DJANGO_ENV=dev uv run python -m pytest analysis/tests/        # NLP (pytest)

cd ../frontend
npm test                                                       # Vitest
```

**Lint:**
```bash
cd backend-django
uv run ruff check .                  # check
uv run ruff check --fix .            # auto-fix
```

**Run dev server bez Dockera:**
```bash
# Terminal 1 — Django
cd backend-django
DJANGO_ENV=dev uv run python manage.py runserver 0.0.0.0:8000

# Terminal 2 — Frontend
cd frontend
npm run dev   # http://localhost:5173
```

## Pułapki

- **`DJANGO_ENV=dev` wymagane do testów** — bez tego settings nie ładują się
  (`config/settings/__init__.py` reads `DJANGO_ENV`). Brak zmiennej = `ModuleNotFoundError`.
- **spaCy Python pin**: `pyproject.toml` ma `requires-python = ">=3.13,<3.14"` — model
  `en_core_web_trf` nie ma jeszcze wheela cp314. uv nie zaktualizuje do 3.14 automatycznie.
- **Docker volume mounts**: NIE bind-mountuj katalogu zawierającego `.venv/` z hosta —
  wersje Pythona mogą się różnić, błędy importu. Dodaj `.venv/` do `.dockerignore` (już jest)
  i używaj zbudowanego obrazu.
- **Alpine healthcheck IPv6**: Alpine `wget localhost:5173` resolves do `::1`, Vite słucha
  IPv4. W healthcheck używaj `127.0.0.1` explicit: `wget -O- http://127.0.0.1:5173`.
- **Frontend rebuild w Docker**: Dockerfile robi `COPY . .` przy buildzie — brak volume mount.
  Zmiana w `frontend/` wymaga `make dev-build && make dev-up`. Dla szybkiego testu używaj
  `npm run dev` na hoście.
- **Nginx location priority w prod**: prefix locations (`/api/`) wymagają `location ^~ /api/`
  żeby mieć priorytet nad regex location (`~* \.(js|css)$`). Bez `^~` request do
  `/api/something.js` matchuje regex (cache) zamiast proxy.
- **Root `.dockerignore`** — istnieje, ale `frontend/.dockerignore` i `backend-django/.dockerignore`
  też. Wszystkie trzy są używane (frontend build z `frontend/`, backend z `backend-django/`).
- **RabbitMQ `definitions.json` wymaga vhosts pierwsze** — patrz [[celery-workers]].
- **Worktree + Docker**: Docker Compose buduje frontend z głównego worktree. Test z secondary
  worktree wymaga manualnego buildu: `docker build -t storyshelf-frontend:local /path/to/worktree/frontend/`
  i restart frontendu w compose.
- **`infra/.env.example` usunięte** — używaj tylko root `.env.example`.
- **Caddy prod używa `tls internal`** (self-signed). W produkcji zmień na Let's Encrypt
  configuration (planowane w ROADMAP "Wdrożenie produkcyjne").
- **Seed.py jest idempotentny** (`get_or_create`) — można puszczać wielokrotnie. Tworzy
  20 książek, 17 autorów, 57 tagów.

## Pytania, na które ta strona odpowiada

- Jak postawić StoryShelf lokalnie?
- Czemu testy nie działają mimo `python manage.py test`?
- Jak zresetować bazę danych w dev?
- Czemu kontener frontend marked unhealthy?
- Jak uruchomić dev server bez Dockera?
- Jak działa `make verify`?
- Czemu spaCy nie instaluje się pod Python 3.14?
- Jak zmienić zawartość seedowanych książek?
- Czemu RabbitMQ nie startuje? (patrz [[celery-workers]])
- Jak postawić Flower bez auth lokalnie? (patrz [[celery-workers]])
