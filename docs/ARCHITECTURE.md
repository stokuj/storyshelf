# Architecture — StoryShelf

## Tech Stack

| Layer              | Technology                                                        |
|--------------------|-------------------------------------------------------------------|
| Frontend           | SvelteKit 2 + Svelte 5 + Tailwind v4 (Node adapter w produkcji)                                  |
| Backend            | Django 6 + Django REST Framework                                  |
| Auth               | JWT — access token w pamięci (reactive singleton), refresh token w HttpOnly cookie |
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
  svelte       # Frontend SSR (Node)
  caddy        # Reverse proxy, SSL
```

---

## Przepływ danych

```
SvelteKit 2 (Node)
    │  JWT: access token → HttpOnly cookie passthrough
    │       refresh token → HttpOnly cookie
    ▼
Caddy  (SSL termination, /api/* → django, /* → svelte)
    ▼
Django + DRF
    │  analyse_book.delay(book_id)
    │  trigger: ręczny — Django Admin action
    ▼
RabbitMQ
    ├──► [queue: ner]   celery-ner   (prefork, CPU-bound)
    │                       └── spaCy en_core_web_trf (CPU-only torch)
    │                               └── BookCharacter/Place/Organization → PostgreSQL
    │                               └── find_pairs() → relations_for_book.delay()
    │
    └──► [queue: llm]   celery-llm   (gevent, I/O-bound)
                            └── OpenRouter API
                                    └── CharacterRelationship → PostgreSQL

Celery result backend: Redis
Failed tasks (max retries) ──► RabbitMQ DLX ──► [queue: dead_letter]
Flower ──► monitoring celery-ner + celery-llm
```

---

## Moduły domenowe

### Auth
- JWT via `djangorestframework-simplejwt`
- Access token: krótkotrwały, tylko w pamięci (reactive singleton, nie localStorage)
- Refresh token: długotrwały, HttpOnly cookie (CSRF-protected)
- Endpointy: `register`, `login`, `token/refresh`, `logout`

### Books
- Model `Book`: tytuł, opis, `avg_rating`, `text` (tymczasowy — czyszczony po NLP)
- Relacje: `Author` (M2M), `Genre` (M2M), `Tag` (M2M)
- Źródło danych: Django Admin (upload TXT do `Book.text`)
- Brak modelu `Chapter` — tekst całej książki w `Book.text`, chunking w workerze

### Reviews & Ratings
- Model `Review`: 1 per User per Book, tekst + ocena (1–5)
- `avg_rating` na `Book` aktualizowany sygnałem Django (`post_save` / `post_delete` na `Review`)

### ShelfEntry
- Statusy: `want_to_read` | `reading` | `read`
- Pola: `start_date`, `finish_date`, `personal_rating`
- `unique_together(user, book)` — jeden wpis na użytkownika na książkę
- Walidacja: `finish_date >= start_date` (Django `clean()`, wywołane w view)

---

## NLP Pipeline

### Trigger
Admin wybiera książki w Django Admin → akcja `Analyse selected books` → `analyse_book.delay(book_id)` per książka.

### analyse_book (kolejka: ner)
```
Book.text
    → chunk_text(chunk_size=400, overlap=50)  # word-based chunking
    → spaCy en_core_web_trf via nlp.pipe()
    → agregacja encji (Counter, NER_MIN_OCCURRENCES=5)
    → upsert BookCharacter / BookPlace / BookOrganization (per book, book FK)
    → find_sentences_with_both_characters()  # regex, synchronicznie
    → Book.text = ""  # czyszczenie
    → relations_for_book.delay(book_id, pairs_data)
```

### relations_for_book (kolejka: llm)
```
pairs_data (pary postaci + zdania z ich współwystępowaniem)
    → LLM (OpenRouter) per para
    → CharacterRelationship.get_or_create() per relacja
    → błędy: log + skip (brak retry)
```

### Modele encji
- `BookCharacter`, `BookPlace`, `BookOrganization` — `unique_together("name", "book")`
- Encje są **per-książka** — nie globalne
- `CharacterRelationship` — 24 typy relacji, `unique_together(from, to, book)`

---

## Workery Celery

### celery-ner — NER Worker
| Parametr     | Wartość                         |
|--------------|---------------------------------|
| Pool         | prefork (CPU-bound)             |
| Queue        | `ner`                           |
| Model NER    | spaCy `en_core_web_trf` (CPU-only torch) |
| Chunking     | 400 słów z overlapem 50         |
| Input        | `book_id`                       |
| Output       | BookCharacter/Place/Org → PostgreSQL |

### celery-llm — LLM Worker
| Parametr     | Wartość                                          |
|--------------|--------------------------------------------------|
| Pool         | gevent (I/O-bound)                               |
| Queue        | `llm`                                            |
| Provider     | OpenRouter API                                   |
| Task         | `relations_for_book(book_id, pairs_data)`        |
| Output       | CharacterRelationship → PostgreSQL               |
| On error     | log + skip para, nie retry                       |

---

## Dead Letter Queue

- **Exchange:** `dlx` (dead letter exchange w RabbitMQ)
- **Queue:** `dead_letter`
- **Obsługa:** inspekcja przez Flower lub management command Django

---

## Schemat bazy danych

```
User
 ├── ShelfEntry (status, personal_rating, start_date, finish_date) ──► Book
 └── Review ──► Book

Book (title, year, isbn, description, page_count, text, avg_rating)
 ├── serie ──► FK "library.Serie" (null, SET_NULL)
 ├── Author (M2M through BookAuthor)
 ├── Genre (M2M through BookGenre)
 └── Tag (M2M through BookTag)

BookCharacter (book FK, name, mention_count) — unique_together(name, book)
BookPlace     (book FK, name, mention_count) — unique_together(name, book)
BookOrganization (book FK, name, mention_count) — unique_together(name, book)

CharacterRelationship
 ├── from_character ──► BookCharacter
 ├── to_character ──► BookCharacter
 ├── relation_type (24 typy)
 └── book ──► Book — unique_together(from, to, book)
```

---

## CI/CD Pipeline

```
git push
    └── GitHub Actions
            ├── lint + testy
            ├── build obrazów Docker
            ├── push do GHCR
            └── SSH → Digital Ocean VPS  (deploy zakomentowany — gotowy do włączenia)
                    └── docker compose pull
                        docker compose up -d --no-deps
```

---

## Kluczowe decyzje architektoniczne

| Decyzja                        | Wybór                              | Uzasadnienie                                                                 |
|--------------------------------|------------------------------------|------------------------------------------------------------------------------|
| NER engine                     | spaCy en_core_web_trf (CPU-only)   | BERT/transformers ~2.5 GB obrazu; spaCy ~400 MB; CPU-only wystarczy dla 5-30 książek |
| Brak modelu Chapter            | Book.text + chunking w workerze    | Chapter był tylko techniką NLP, nie domeną; upraszcza schemat                |
| Encje per-book                 | book FK + unique_together          | Globalny unique name powodował kolizje między książkami                       |
| 2 taski Celery                 | analyse_book + relations_for_book  | Było 5 tasków z race condition; uproszczenie bez utraty funkcjonalności       |
| Broker vs result backend       | RabbitMQ (broker) + Redis (wyniki) | RabbitMQ: routing, DLQ, niezawodność; Redis: szybki odczyt wyników            |
| Dwa oddzielne workery Celery   | prefork (NER) + gevent (LLM)       | spaCy jest CPU-bound; OpenRouter to I/O — różne modele współbieżności         |
| Access token w pamięci         | SvelteKit SSR cookie passthrough    | Odporność na XSS; refresh w HttpOnly cookie chroni przed CSRF                |

---

## Rekomendacje (roadmapa)

| Faza   | Zakres                                                              |
|--------|---------------------------------------------------------------------|
| MVP    | Brak rekomendacji                                                   |
| Faza 2 | Collaborative filtering na podstawie ocen użytkowników              |
| Faza 3 | Hybryda: collaborative + content-based (encje NER jako features)    |
