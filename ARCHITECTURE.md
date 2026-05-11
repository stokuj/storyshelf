# Architecture — Goodreads Clone

## Tech Stack

| Layer              | Technology                                                        |
|--------------------|-------------------------------------------------------------------|
| Frontend           | Vue 3 + Vite (Nginx w produkcji)                                  |
| Backend            | Django 5 + Django REST Framework                                  |
| Auth               | JWT — access token w pamięci Pinia, refresh token w HttpOnly cookie |
| Message broker     | RabbitMQ (z dead letter exchange)                                 |
| Result backend     | Redis                                                             |
| Async workers      | Celery                                                            |
| Worker monitoring  | Flower                                                            |
| Baza danych        | PostgreSQL 16 (JSONB dla wyników NER/LLM)                         |
| Reverse proxy      | Caddy (SSL termination, routing)                                  |
| CI/CD              | GitHub Actions → GHCR → Digital Ocean VPS                        |
| Deployment         | Docker Compose na VPS                                             |

---

## Kontenery

```
services:
  db           # PostgreSQL 16
  redis        # Celery result backend
  rabbitmq     # Message broker (z dead letter exchange)
  django       # Core API — DRF, JWT, auth, books, reviews
  celery-ner   # NER worker (prefork pool, CPU-bound)
  celery-llm   # LLM worker (gevent pool, I/O-bound)
  flower       # Monitoring Celery (wszystkie workery)
  vue          # Frontend SPA (Nginx)
  caddy        # Reverse proxy, SSL
```

---

## Przepływ danych

```
Vue 3 (Nginx)
    │  JWT: access token → Pinia (pamięć)
    │       refresh token → HttpOnly cookie
    ▼
Caddy  (SSL termination, /api/* → django, /* → vue)
    ▼
Django + DRF
    │  .apply_async()
    │  trigger: ręczny — Django Admin action
    ▼
RabbitMQ
    ├──► [queue: ner]   celery-ner   (prefork, CPU-bound)
    │                       └── dslim/bert-base-NER
    │                               └── NERResult (JSONB) → PostgreSQL
    │
    └──► [queue: llm]   celery-llm   (gevent, I/O-bound)
                            └── OpenRouter API
                                    └── BookSummary (JSONB) → PostgreSQL

Celery result backend: Redis
Failed tasks (max retries) ──► RabbitMQ DLX ──► [queue: dead_letter]
Flower ──► monitoring celery-ner + celery-llm
```

---

## Moduły domenowe

### Auth
- JWT via `djangorestframework-simplejwt`
- Access token: krótkotrwały, tylko w pamięci Pinia (nie localStorage)
- Refresh token: długotrwały, HttpOnly cookie (CSRF-protected)
- Endpointy: `register`, `login`, `token/refresh`, `logout`

### Books
- Model `Book`: tytuł, opis, okładka, `avg_rating`
- Relacje: `Author` (M2M), `Genre` (M2M)
- Źródło danych: OpenLibrary API (import skryptem) + Django Admin (ręcznie)
- Brak modelu `Edition` — jedna encja `Book` per dzieło; dedulikacja przy imporcie

### Reviews & Ratings
- Model `Review`: 1 per User per Book, tekst + ocena (1–5)
- `avg_rating` na `Book` aktualizowany sygnałem Django (`post_save` / `post_delete` na `Review`)
- Trigger NER/LLM: ręcznie przez admina via Django Admin action

### UserBook
- Statusy: `want_to_read` | `reading` | `read`
- Pola: `start_date`, `finish_date`, `personal_rating`

---

## Workery Celery

### celery-ner — NER Worker
| Parametr     | Wartość                         |
|--------------|---------------------------------|
| Pool         | prefork (CPU-bound)             |
| Queue        | `ner`                           |
| Model NER    | `dslim/bert-base-NER` (English) |
| Routing      | `NERRouter` — wybór modelu per język (gotowe na rozszerzenie) |
| Input        | Tekst recenzji lub opis książki |
| Output       | Lista encji → `NERResult` (JSONB) w PostgreSQL |
| Retry policy | Max 3 próby, exponential backoff |
| On failure   | → Dead Letter Queue             |

### celery-llm — LLM Worker
| Parametr     | Wartość                                          |
|--------------|--------------------------------------------------|
| Pool         | gevent (I/O-bound)                               |
| Queue        | `llm`                                            |
| Provider     | OpenRouter API                                   |
| Taski        | `summarize_book(book_id)`, `summarize_reviews(book_id)` |
| Output       | Tekst → `BookSummary` (JSONB) w PostgreSQL       |
| Retry policy | Max 3 próby, exponential backoff                 |
| On failure   | → Dead Letter Queue                              |

---

## Dead Letter Queue

- **Exchange:** `dlx` (dead letter exchange w RabbitMQ)
- **Queue:** `dead_letter`
- **Warunek trafienia:** task przekroczył limit prób (NER lub LLM)
- **Obsługa:** inspekcja przez Flower lub management command Django; ponowienie ręczne

---

## Schemat bazy danych

```
User
 ├── UserBook (status, personal_rating, start_date, end_date) ──► Book
 └── Review ──► Book

Book
 ├── Author (M2M)
 ├── Genre (M2M)
 ├── BookSummary   (JSONB — wynik LLM)
 └── NERResult     (JSONB — encje z opisu książki)

Review
 └── NERResult     (JSONB — encje z tekstu recenzji)
```

---

## CI/CD Pipeline

```
git push
    └── GitHub Actions
            ├── lint + testy
            ├── build obrazów Docker
            ├── push do GHCR
            └── SSH → Digital Ocean VPS
                    └── docker compose pull
                        docker compose up -d --no-deps
```

---

## Kluczowe decyzje architektoniczne

| Decyzja                        | Wybór                              | Uzasadnienie                                                                 |
|--------------------------------|------------------------------------|------------------------------------------------------------------------------|
| Broker vs result backend       | RabbitMQ (broker) + Redis (wyniki) | RabbitMQ daje routing, DLQ, niezawodność; Redis szybki do odczytu wyników    |
| Dwa oddzielne workery Celery   | prefork (NER) + gevent (LLM)       | BERT jest CPU-bound; wywołania OpenRouter to I/O — różne modele współbieżności |
| JSONB dla NER/LLM              | PostgreSQL JSONB                   | Elastyczny schemat dla nieregularnych danych AI bez dodatkowego store'u       |
| Brak modelu Edition            | Jedna `Book` per dzieło            | Upraszcza MVP; dedulikacja obsługiwana na warstwie importu                   |
| Trigger NER/LLM ręczny         | Django Admin action                | Eliminuje niekontrolowane wywołania async na wczesnym etapie                 |
| Access token w pamięci         | Pinia (nie localStorage)           | Odporność na XSS; refresh w HttpOnly cookie chroni przed CSRF                |
| Dead Letter Queue              | RabbitMQ DLX                       | Failed taski nie znikają po cichu; umożliwia inspekcję i ponowienie          |

---

## Rekomendacje (roadmapa)

| Faza   | Zakres                                                              |
|--------|---------------------------------------------------------------------|
| MVP    | Brak rekomendacji                                                   |
| Faza 2 | Collaborative filtering na podstawie ocen użytkowników              |
| Faza 3 | Hybryda: collaborative + content-based (encje NER jako features)    |
