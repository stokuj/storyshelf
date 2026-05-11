# storyshelf

A full-stack book tracking and literary analysis platform.

- **backend/** — Java Spring Boot REST API (book catalog, users, bookshelf, reviews, series)
- **frontend/** — Vue 3 SPA with Tailwind/daisyUI
- **nlp-service/** — Python FastAPI microservice for NER, character extraction, and LLM-based relation analysis
- **infra/** — Docker Compose, Caddy config, deploy scripts, shared .env.example

## Quick Start (Dev)

```bash
cp infra/.env.example .env
# edit .env with your keys
make dev-up
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8080
- NLP Service: http://localhost:8000
- Swagger/OpenAPI: http://localhost:8080/docs
- Kafka Console: http://localhost:8081

## Production

```bash
cp infra/.env.example .env
# edit .env with production values
make prod-up
make prod-logs
```

## Architecture

```
Browser → Caddy (reverse proxy) → Frontend (Vue 3 SPA)
                                → Backend (Spring Boot + PostgreSQL)
                                → NLP Service (FastAPI + Celery + Redis + Kafka)
```

Frontend talks to Backend via REST. Backend communicates with NLP Service asynchronously via Kafka for book analysis (NER, character extraction, relation extraction).

## Documentation

- [API Endpoints](docs/backend/api_endpoints.md)
- [Database Schema](docs/backend/database.md)
- [NLP Data Flow](docs/backend/data_flow.md)
- [User Stories](docs/backend/user_stories.md)
- [NLP Testing Guide](docs/nlp-service/request_examples.md)
