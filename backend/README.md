# springshelf

A book tracking and recommendation app inspired by Goodreads. Built with Java Spring Boot, FastAPI (Python ML microservice), Docker, and GitHub Actions. Features will include OAuth2 authentication, book ratings and reviews, and a recommendation engine. The project documents my learning journey with the Spring ecosystem and event-driven architecture.

## Project structure

- `src/main/java/` - Spring Boot backend (REST API + page controllers)
- `src/main/resources/templates/` - Thymeleaf-served frontend
- `src/main/resources/application.properties` - app and OAuth2 configuration

## User Stories

### Current State

#### GUEST

As a GUEST I can register a new account at /register.
As a GUEST I can log in with email/password or GitHub at /login.
As a GUEST I can browse the book catalog at /.
As a GUEST I can view book details at /book/{id}.

#### USER

As a USER I can log out via the navbar.
As a USER I can add a book to my shelf with a reading status at /book/{id}.
As a USER I can change the reading status of a book on my shelf at /bookshelf.
As a USER I can remove a book from my shelf at /bookshelf.
As a USER I can filter my shelf by reading status at /bookshelf.
As a USER I can upload a .txt file with book content at /book/{id} to trigger background analysis.

### TODO

#### GUEST

As a GUEST I can search for books by title, author or genre at /.
As a GUEST I can view a public user profile at /profile/{username}.

#### USER

As a USER I can view detected characters for a book at /book/{id}.
As a USER I can view character relationships for a book at /book/{id}.
As a USER I can view chapter statistics (word count, token count) at /book/{id}.
As a USER I can rate a book and write a review at /book/{id}.
As a USER I can edit my profile (username, bio, avatar) at /settings.
As a USER I can set my profile as public or private at /settings.
As a USER I can submit a book proposal at /books/propose.
As a USER I can check the status of my proposal (pending / approved / rejected) at /books/proposals.

#### MODERATOR

As a MODERATOR I can add a book directly to the catalog at /admin/books/new.
As a MODERATOR I can edit book details at /admin/books/{id}/edit.
As a MODERATOR I can approve or reject a book proposal at /admin/proposals.
As a MODERATOR I can edit a proposed book before approving it at /admin/proposals/{id}/edit.
As a MODERATOR I can manually trigger analysis for a book at /admin/books/{id}.
As a MODERATOR I can delete a user review at /admin/reviews.
As a MODERATOR I can view a private user profile at /admin/users/{id}.

#### ADMIN

As an ADMIN I can do everything a MODERATOR can.
As an ADMIN I can manage users (assign roles, ban accounts) at /admin/users.
As an ADMIN I can delete a user account at /admin/users/{id}.
As an ADMIN I can monitor system health (Celery, Kafka, queues) at /admin/system.
As an ADMIN I can delete a book from the catalog at /admin/books/{id}.

## Changelog

### [0.5.0] - 2026-03-19

Kafka flow and book-level results.

#### Added

- Book fields for aggregation: `chaptersCount`, `nerCompletedCount`, `characters`, `findPairsResult`, `relationsResult`.
- Book-level callbacks for find-pairs and relations.

#### Changed

- Manual `POST /api/fastAPI/chapters/{chapterId}/analyse` and `/ner` now send Kafka events and return 202.
- find-pairs and relations results are saved on the book, not on chapters.

### [0.4.1] - 2026-03-15

Manual FastAPI endpoints for per-chapter analysis.

#### Added

- FastAPI find-pairs client method and request DTO.
- `POST /api/NER/chapters/{chapterId}/find-pairs` to run find-pairs for a single chapter.
- Manual NER and analysis endpoints for single chapters.

#### Changed

- Disabled automatic NER and analysis calls during chapter load.

### [0.4.0] - 2026-03-12

Deploy and CI. Move infrastructure config to Docker and Caddy.

#### Added

- CI for SpringShelf: tests, image build, and SSH deploy.
- H2-based test profile so tests do not need Postgres.

#### Changed

- Production compose now includes the full stack (SpringShelf + StoryWeave + DB + Redis + Caddy).
- Caddy routes /storyweave and defaults to SpringShelf.
- Dev compose exposes port 8080 on the host and does not use Caddy.

### [0.3.1] - 2026-03-11

Docker and env cleanup plus partial book updates.

#### Added

- `PATCH /api/books/{id}` for partial book updates.
- Example `.env.example` for running via Docker Compose.

#### Changed

- `docker-compose.yml`: improved service config, DB healthcheck, persistent volume, and pinned Postgres 16 image.
- `application.properties`: environment variable support for DB and `jwt.secret`.

#### Removed

- `src/main/resources/application-local.properties` (local config moved to env).

### [0.3.0] - 2026-03-05

Frontend migration to Thymeleaf and cleaned up web/API auth flow.

#### Added

- Thymeleaf views: `home`, `book`, `bookshelf`, `login`, `register`, `settings`, `error`, plus a base layout.
- `PageController` for pages, login/register, and bookshelf actions via HTML forms.
- `UserDetailsServiceImpl` for session-based login (form login).

#### Changed

- Removed the old SPA frontend (`frontend/`) based on static HTML + JS and a token in `localStorage`.
- Split security into two chains:
  - `/api/**` - JWT + stateless,
  - web (`/**`) - session + form login + OAuth2.
- OAuth2 success flow logs the user into a session and redirects to `/`.
- `GlobalExceptionHandler` returns JSON for `/api/**` and renders `error.html` for web pages.

#### Fixed

- Fixed login-dependent rendering in templates (`sec:authorize`).
- Fixed anonymous user detection in `PageController`.
- The home page (`/`) no longer shows the `+ Add` action to guests.

### [0.2.1] - 2026-03-04

Expanded book model and cleanup.

#### Added

- New `Book` fields: `isbn`, `description`, `pageCount`, `genres`, `tags`, `rating`, `ratingsCount`, `createdAt`, `updatedAt`.
- `book_genres` and `book_tags` tables for filtering by genres and tags.

#### Changed

- `BookService` refactor: extracted DTO-to-entity mapping into `mapRequestToBook()`.
- Removed `category` from the model (replaced by `genres`).
- Removed `rating` and `ratingsCount` from `BookRequest` so clients cannot set ratings manually.

#### Fixed

- Fixed duplicate `.gitignore` entries.
- Removed `styles.css` from git tracking.
- Fixed the parameter name in `setIsbn()`.

### [0.2.0] - 2026-03-03

Working prototype with frontend.

#### Added

- Separate frontend based on Node.js + Tailwind + daisyUI.
- Simple pages: base, settings, login, register.
- Backend models for books, user books, and users.

![img.png](img.png)

### [0.1.1] - 2026-03-02

Working prototype with Swagger UI.

#### Added

- Login and registration.
- GitHub login.
- Env vars for the `local` profile in `application-local.properties` (`.gitignore`).
- JWT-based auth.

![img_1.png](img_1.png)

### [0.1.0] - 2026-03-02

First working backend version.

#### Added

- Spring Boot 4 + Java 21 project scaffold.
- PostgreSQL connection configuration.
- `Book` model and `BookRepository`.
- Business logic in `BookService`.
- REST API in `BookController` (`GET`, `POST`, `PUT`, `DELETE`).
- Payload validation via `BookRequest`.
- Global error handler (`GlobalExceptionHandler`).
- Containerized app and database.
