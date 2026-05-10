# Django Migration Design

**Status:** Approved  
**Date:** 2026-05-10  
**Replaces:** Spring Boot backend → Django + DRF  
**Scope:** Backend only. Frontend (Vue 3), NLP (FastAPI), and PostgreSQL — unchanged.

---

## 1. Architecture Overview

### Before → After

```
BEFORE:                              AFTER:

┌──────────┐                         ┌──────────┐
│  Caddy   │                         │  Caddy   │  (unchanged)
└────┬─────┘                         └────┬─────┘
     │                                   │
  ┌──┴──────────────────────┐        ┌──┴──────────────────────┐
  │  :80                    │        │  :80                    │
  │  /api/*   → backend:8080│        │  /api/*   → django:8000 │
  │  /*       → frontend:5173│       │  /*       → frontend:5173│
  └─────────────────────────┘        └─────────────────────────┘
     │          │                         │          │
┌────┴───┐ ┌───┴──────┐           ┌──────┴───┐ ┌───┴──────┐
│ Spring │ │  Vue 3   │           │  Django   │ │  Vue 3   │
│ Boot   │ │ frontend │           │  + DRF    │ │ frontend │
│ :8080  │ │ :5173    │           │  :8000    │ │ :5173    │
└──┬──┬──┘ └──────────┘           └──┬──┬─────┘ └──────────┘
   │  │                              │  │
   │  │  Kafka ◄────────┐            │  │  RabbitMQ ◄───────┐
   │  │  (4 topics)     │            │  │  (1 queue)        │
   │  └─────────────────┤            │  └───────────────────┤
   │                    │            │                      │
   │  ┌─────────────────┘            │  ┌───────────────────┘
   │  │                              │  │
┌──┴──┴─────┐                  ┌─────┴──┴──────┐
│ FastAPI   │                  │ FastAPI NLP   │  (unchanged)
│ NLP       │                  │ + Celery work │
│ :8000     │                  │ :8000         │
└───────────┘                  └───────────────┘

Communication:
  Before: Spring ⇄ Kafka ⇄ NLP (two-language consumers, manual offsets)
  After:  Django ──HTTP──→ NLP (Celery task fires POST)
          NLP    ──HTTP──→ Django (callback endpoint, Celery retries built-in)
```

### Removed
- Spring Boot (entire JVM backend)
- Kafka + ZooKeeper (2 containers)
- 3 AdminView Vue components (replaced by Django Admin)
- Manual Kafka consumers in 2 languages

### Added
- Django + DRF — 6 apps
- RabbitMQ — 1 container (replaces Kafka + ZooKeeper)
- Celery worker — 1 container
- 4 callback endpoints in Django (`/api/internal/*`)

---

## 2. Django Project Structure (6 Apps)

```
backend-django/
├── config/                    # Django project
│   ├── settings/
│   │   ├── base.py            # shared settings
│   │   ├── dev.py             # DEBUG=True, console email
│   │   └── prod.py            # DEBUG=False, SMTP, Sentry
│   ├── urls.py                # root URL router
│   ├── celery.py              # Celery app config
│   └── wsgi.py
│
├── users/                     # app 1 — User, UserFollow, auth
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
│
├── books/                     # app 2 — Book, Chapter, StoryCharacter, relations
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
│
├── reviews/                   # app 3 — Review
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── admin.py
│
├── shelf/                     # app 4 — ShelfEntry
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── admin.py
│
├── library/                   # app 5 — Author, BookAuthor, BookGenre, Tag, Series
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── admin.py
│
├── analysis/                  # app 6 — Celery tasks, pipeline, callback endpoints
│   ├── tasks.py
│   ├── callbacks.py
│   ├── pipeline.py
│   └── urls.py
│
├── Dockerfile
├── requirements.txt
└── manage.py
```

### Model Relationships (app ↔ app, ForeignKey)

```
users.User ──→ shelf.ShelfEntry        (user_id FK)
users.User ──→ reviews.Review           (user_id FK)
users.User ──→ users.UserFollow         (self-referential FK)
books.Book ──→ shelf.ShelfEntry         (book_id FK)
books.Book ──→ reviews.Review           (book_id FK)
books.Book ──→ library.BookAuthor       (FK)
books.Book ──→ library.BookGenre        (FK)
library.Author ──→ library.BookAuthor   (FK)
library.Series ──→ books.Book           (series_id FK, nullable)
books.Chapter ──→ books.Book            (book_id FK)
books.BookCharacter ──→ books.Book, books.StoryCharacter (FK)
books.CharacterRelation ──→ books.Book, books.StoryCharacter (source, target FK)
```

---

## 3. API & Auth

### 3.1 JWT Auth (DRF simplejwt)

| Method | Path | Body | Response |
|--------|------|------|----------|
| POST | `/api/auth/register/` | `{username, email, password}` | 201 `{access, refresh}` |
| POST | `/api/auth/login/` | `{email, password}` | 200 `{access, refresh}` |
| POST | `/api/auth/refresh/` | `{refresh}` | 200 `{access}` |
| GET | `/api/auth/me/` | — | `{authenticated, email, username, role}` |
| POST | `/api/auth/logout/` | `{refresh}` | 200 (blacklists refresh token) |

### 3.2 API Endpoints

| App | Endpoints |
|-----|-----------|
| **users** | `POST /api/auth/register/`, `/login/`, `/refresh/`, `/logout/` |
| | `GET /api/auth/me/`, `GET /api/users/{username}/` |
| | `GET/PUT /api/users/me/`, `PATCH /api/users/me/visibility/` |
| | `POST/DELETE /api/users/{username}/follow/` |
| | `GET /api/users/{username}/followers/`, `/following/` |
| **books** | `GET /api/books/`, `POST /api/books/` |
| | `GET/PUT/PATCH/DELETE /api/books/{id}/` |
| | `GET /api/books/{id}/details/` (aggregated) |
| | `POST/GET/DELETE /api/books/{id}/chapters/` |
| | `GET /api/books/{id}/characters/`, `/relations/` |
| **reviews** | `GET/POST /api/books/{id}/reviews/` |
| | `DELETE /api/reviews/{id}/` (moderator) |
| **shelf** | `GET/POST /api/shelf/` |
| | `GET/PATCH/DELETE /api/shelf/{bookId}/` |
| **library** | `GET/POST /api/authors/`, `GET/PUT/DELETE /api/authors/{id}/` |
| | `GET/POST /api/series/`, `GET/PUT/DELETE /api/series/{id}/` |
| **analysis** | `POST /api/internal/chapters/{id}/analyse-result/` (callback, not exposed) |
| | `POST /api/internal/chapters/{id}/ner-result/` (callback) |
| | `POST /api/internal/books/{id}/find-pairs-result/` (callback) |
| | `POST /api/internal/books/{id}/relations-result/` (callback) |

`/api/internal/*` endpoints are internal Docker network only — not routed through Caddy.
Security is enforced by a Django middleware that checks `REMOTE_ADDR` against the Docker network CIDR
(`172.16.0.0/12`). Requests from outside the Docker network receive 403. Additionally, Caddy has an
explicit `respond /api/internal/* 403` rule as a second layer of defense.

### 3.3 Key Differences vs Spring

- LoginRequest: DRF serializer accepts `email` only (Spring also accepted `username` as alias). Frontend already sends `email` — no change.
- BookDetailResponse: Aggregated via `SerializerMethodField` + `prefetch_related`.
- Chapter upload: DRF `FileUploadParser` / `request.FILES` instead of Spring `MultipartFile`.
- Private profiles: Returns 404 (not 403) when profile is private, matching current behavior.

---

## 4. Celery Analysis Pipeline

### Flow

```
1. MODERATOR uploads chapter file
   POST /api/books/{id}/chapters/
   └─ Splits text into chapters, saves to DB
   └─ For EVERY chapter: analyse_chapter.delay(chapter_id, content) ──HTTP→ NLP
   └─ For CHAPTER 1 only:  ner_chapter.delay(chapter_id, content)    ──HTTP→ NLP

2. NLP completes analyse → callback
   POST /api/internal/chapters/{id}/analyse-result/
   └─ Saves char_count, word_count, token_count to Chapter
   └─ Sets chapter.analysis_completed = True

3. NLP completes NER → callback
   POST /api/internal/chapters/{id}/ner-result/
   └─ Saves ner_result (JSONB) to Chapter
   └─ Atomic increment: Book.ner_completed_count += 1 (via F() expression)
   └─ If ner_completed_count >= chapters_count:
        find_pairs.delay(book_id) ──HTTP→ NLP

4. NLP finds character pairs → callback
   POST /api/internal/books/{id}/find-pairs-result/
   └─ Creates StoryCharacterRelation rows (source, target)
   └─ relations_for_book.delay(book_id) ──HTTP→ NLP

5. NLP extracts relations → callback
   POST /api/internal/books/{id}/relations-result/
   └─ Fills in relation, evidence, confidence in CharacterRelation
   └─ DONE
```

### Tasks (`analysis/tasks.py`)

All tasks use `bind=True`, `max_retries=3`, `default_retry_delay=10`.
Each task sends HTTP POST to NLP service, does not wait for result (callback handles response).

- `analyse_chapter(chapter_id, content)` — POST to `/chapters/{id}/analyse`
- `ner_chapter(chapter_id, content)` — POST to `/chapters/{id}/ner`
- `find_pairs(book_id)` — gathers full text + character map, POST to `/books/{id}/find-pairs`
  - **Payload size note:** Full concatenated book text can be several MB (e.g. 500-page novel ~2-3 MB).
    HTTP timeout is set to 60s on the Celery task side. NLP service must accept large payloads.
    If this becomes a bottleneck, future optimization would be chunked upload via multiple requests.
- `relations_for_book(book_id)` — gathers unresolved pairs, POST to `/books/{id}/relations`

### Callback Idempotency (`analysis/callbacks.py`)

Each callback checks if already processed before applying changes:
- Analyse: `chapter.analysis_completed` guard
- NER: `chapter.ner_result` guard, `select_for_update()` on increment
- Find-pairs: `CharacterRelation.objects.filter(book_id=book_id).exists()` guard
- Relations: checks if `relation` field already filled (non-blank)

### Celery vs Kafka Comparison

| | Kafka (before) | Celery (after) |
|---|---|---|
| Retry | Manual FixedBackOff | `max_retries=3`, exponential backoff built-in |
| Monitoring | None | Flower dashboard |
| Idempotency | Manual if-checks | Same if-checks in callbacks |
| Queuing | Topic + partition | RabbitMQ queue |
| Dead letter | Manual DLT | Celery native after max_retries |

---

## 5. Django Admin

### Replaces Vue Admin Views

| Vue Admin View (removed) | Django Admin replacement |
|---|---|
| AdminBooksView | `BookAdmin` with inlines: ChapterInline, BookAuthorInline, BookCharacterInline |
| AdminAuthorsView | `AuthorAdmin` |
| AdminSeriesView | `SeriesAdmin` |
| Delete review (moderator) | `ReviewAdmin.list_filter` by rating + delete action |
| User management | `UserAdmin` — role assignment, ban (is_active), password reset |

### What Stays in Vue (user-facing)

- HomeView, BookDetailView, BookshelfView, ProfileView, SettingsView
- LoginView, RegisterView (updated for JWT)

### Removed from Vue

- `AdminBooksView.vue`, `AdminAuthorsView.vue`, `AdminSeriesView.vue`
- Router paths `/admin/*`

---

## 6. Frontend Changes

### `api.js` — JWT Interceptors

Add JWT token management: `setTokens()`, `refreshAccessToken()`, `Authorization: Bearer` header.

Intercept 401 responses → attempt refresh → on failure, redirect to login.

### JWT Token Storage

Access and refresh tokens are stored in `localStorage` for simplicity. This is the standard
approach for SPAs using DRF simplejwt and keeps the `api.js` interceptor straightforward.
**Known trade-off:** `localStorage` is accessible to JavaScript, making tokens vulnerable to XSS.
Mitigations: strict Content Security Policy (CSP), input sanitization in Vue, short access token
lifetime (30 min). An httpOnly cookie approach would require a thin backend proxy (`/api/auth/refresh/`
via cookie) and is noted as a future hardening option, not required for initial migration.

### Changed Files

| File | Change |
|------|--------|
| `api.js` | +JWT interceptors, -`credentials: 'include'`, +`setTokens`/`refresh` |
| `LoginView.vue` | Handle new response shape `{access, refresh}` |
| `RegisterView.vue` | Same |
| `router.js` | Remove admin routes |

### Removed Files

| File | Reason |
|------|--------|
| `AdminBooksView.vue` | → Django Admin |
| `AdminAuthorsView.vue` | → Django Admin |
| `AdminSeriesView.vue` | → Django Admin |

All 32 `api.js` exported functions keep same signatures. Only the internal `request()` wrapper changes.

---

## 7. Infrastructure

### Docker Compose Services (8 → 7)

| Before | After |
|--------|-------|
| backend (Spring) | django (Django + DRF) |
| nlp-service (FastAPI) | nlp-service (FastAPI, unchanged) |
| frontend (Vue) | frontend (Vue, unchanged) |
| kafka | rabbitmq |
| zookeeper | — |
| redis | redis (Celery result backend + cache) |
| db (PostgreSQL) | db (PostgreSQL, unchanged) |
| caddy | caddy (updated upstream) |
| — | celery-worker (new) |

### django service
- Built from `backend-django/Dockerfile`
- `gunicorn config.wsgi -b 0.0.0.0:8000 -w 4` (2×CPU+1 for a 2-core container)
- Env: `DATABASE_URL`, `CELERY_BROKER_URL`, `NLP_SERVICE_URL`, `SECRET_KEY`, JWT lifetime settings

### celery-worker service
- Same image as django
- `celery -A config worker -l info -c 4`
- Same env as django

### rabbitmq service
- `rabbitmq:4-management-alpine`
- Port `15672` (management UI) bound to `127.0.0.1:15672`
- Port `5672` (AMQP) internal only

### NLP service
- Zero code changes. Receives HTTP from Celery instead of Kafka.
- Callback URL: `http://django:8000/api/internal/`

### Caddy
```diff
- reverse_proxy backend:8080
+ reverse_proxy django:8000
```

### Environment Variables (new)

```
DJANGO_SECRET_KEY=<generated>
DATABASE_URL=postgres://postgres:secret@db:5432/booksdb
CELERY_BROKER_URL=amqp://rabbitmq:5672//
NLP_SERVICE_URL=http://nlp-service:8000
CALLBACK_BASE_URL=http://django:8000
JWT_ACCESS_LIFETIME_MINUTES=30
JWT_REFRESH_LIFETIME_MINUTES=1440
```

---

## 8. Git Strategy

- New folder `backend-django/` alongside existing `backend/` (Spring)
- Both live in parallel until Django is complete and tested
- After migration complete: delete `backend/`, rename `backend-django/` → `backend/`
- All work on a dedicated feature branch

### Data Migration

This is a **fresh start** — no production data exists yet. The database will be created from scratch
via `python manage.py migrate`. The existing Flyway migration (`V1__init_schema.sql`) serves as a
reference for the Django model definitions but no data needs to be ported. Seed data (if any) will
be recreated via Django management commands or fixtures.

---

## 9. Technology Stack

| Component | Before | After |
|-----------|--------|-------|
| Language | Java 21 | Python 3.13 |
| Framework | Spring Boot 4.0.3 | Django 5.x |
| API | Spring MVC | Django REST Framework |
| Auth | HTTP Sessions (JSESSIONID) | JWT (simplejwt) |
| ORM | JPA/Hibernate | Django ORM |
| Migrations | Flyway | Django migrations |
| Broker | Kafka | RabbitMQ |
| Task queue | Manual Kafka consumers | Celery |
| Admin panel | Vue components | Django Admin |
| API docs | Springdoc | drf-spectacular |
| Container count | 8 | 7 |

---

## 10. What Does NOT Change

- Vue 3 frontend (except `api.js` JWT interceptors and 3 removed admin views)
- FastAPI NLP microservice (receives HTTP instead of Kafka)
- PostgreSQL database schema (recreated via Django migrations — fresh start, no data to port)
- Caddy routing (only upstream service name changes)
- Redis (stays as Celery result backend and cache)
