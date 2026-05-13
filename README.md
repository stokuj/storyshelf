# StoryShelf

Full-stack book tracking and literary analysis platform. Django REST API + Vue 3 SPA, orchestrated via Docker Compose. NER and LLM engines run inside Celery workers.

## Architecture

```
Browser → Vite dev proxy (5173) → Django (8000) → PostgreSQL
                                  → RabbitMQ → celery-ner (prefork) / celery-llm (gevent)
                                  → Redis
         ↔ Flower (5555) — Celery monitoring
```

## Quick Start

```bash
# 1. Copy and edit environment variables
cp .env.example .env
# At minimum set OPENROUTER_API_KEY for NLP features

# 2. Start all services
make dev-up

# 3. Seed test data (optional)
docker compose -f infra/compose/docker-compose.dev.yml exec django python ../infra/scripts/seed.py
```

**Dev URLs:**
- Frontend: http://localhost:5173
- Django API: http://localhost:8000
- API Documentation: http://localhost:8000/api/docs/
- Flower (Celery monitoring): http://localhost:5555
- RabbitMQ Management: http://127.0.0.1:15672

## Project Structure

| Directory | Purpose |
|-----------|---------|
| `backend-django/` | Django 5 + Django REST Framework + Celery |
| `frontend/` | Vue 3 + Vite + Tailwind CSS + daisyUI |
| `infra/` | Docker Compose, Caddy config, deploy scripts, RabbitMQ definitions |
| `docs/` | Architecture docs, plans, specs |

## Development Commands

### Backend

```bash
cd backend-django/
uv run python manage.py migrate
uv run python manage.py runserver 0.0.0.0:8000
uv run python manage.py test
uv run ruff check .
```

### Frontend

```bash
cd frontend/
npm run dev      # port 5173
npm run build
npm test
```

### Docker Compose

```bash
make dev-up      # start all services
make dev-down    # stop all services
make dev-build   # rebuild images
make prod-up     # production mode
make prod-logs   # production logs
```

## Tech Stack

- **Backend:** Django 5, Django REST Framework, SimpleJWT, Celery, PostgreSQL 16, Redis, RabbitMQ
- **Frontend:** Vue 3, Vue Router, Vite, Tailwind CSS, daisyUI
- **NLP:** BERT (NER), OpenRouter LLM API, Celery workers
- **Infra:** Docker Compose, Caddy (reverse proxy), Flower (Celery monitoring)

## Key Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | yes | For LLM-based relation extraction |
| `DJANGO_SECRET_KEY` | yes | Django secret key |
| `DJANGO_ENV` | yes | `dev` or `prod` |
| `DATABASE_URL` | yes | PostgreSQL connection string |
| `CELERY_BROKER_URL` | yes | RabbitMQ URL |

See `.env.example` for full list.

## Documentation

- [Architecture](ARCHITECTURE.md) — system design and data flow
- [AGENTS.md](AGENTS.md) — development conventions and commands
- `docs/superpowers/` — implementation plans and design specs

## License

MIT
