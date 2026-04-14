# springshelf

A book tracking and recommendation app inspired by Goodreads. Built with Java Spring Boot, FastAPI (Python ML microservice), Docker, and GitHub Actions. Features will include OAuth2 authentication, book ratings and reviews, and a recommendation engine. The project documents my learning journey with the Spring ecosystem and event-driven architecture.

## Documentation

For detailed information about the project, please refer to the following documents:

- [User Stories](backend/docs/user_stories.md) - functional requirements and role definitions.
- [Project Structure](backend/docs/project_structure.md) - overview of the directory and package layout.
- [Database Schema](backend/docs/database.md) - Mermaid diagram of the database entities and relationships.

## Development Compose

Run one of the three development variants:

- Base (without ML services): `docker compose -f docker-compose.dev.yml up -d`
- Full with local ML build: `docker compose -f docker-compose.dev.build.yml up -d --build`
- Full with pulled ML images: `docker compose -f docker-compose.dev.pull.yml up -d`

---

## Changelog

### [0.6.0] - 2026-03-23

API stabilization, validation, and documentation.

#### Added

- Full OpenAPI/Swagger documentation for all REST controllers with clear English descriptions and response codes.
- Comprehensive input validation using Jakarta Validation (`@Valid`, `@NotBlank`, `@Min`, `@Max`, `@Size`) across all API request DTOs.
- Structured validation error responses in `GlobalExceptionHandler` (returns 400 Bad Request with field-specific error messages).
- Complete integration test skeleton structure in `src/test/java/com/stokuj/books/controller/` with `// TODO` items for every API endpoint.
- New `AuthorRequest` and `SeriesRequest` DTOs to replace raw entity usage in admin controllers.

#### Changed

- Reorganized API package structure: moved user-specific controllers (`UserController`, `UserFollowController`, `BookShelfController`) to `com.stokuj.books.controller.api.user`.
- Refactored `AdminAuthorController` and `AdminSeriesController` to use DTOs, closing mass-assignment security vulnerabilities.
- Standardized API response codes and summaries in Swagger UI.

### [0.5.2] - 2026-03-21

Endpoint routing and package reorganization.

#### Added

- Flyway migration `V7__add_book_version.sql` to ensure `books.version` exists in every environment.

#### Changed

- Split controllers into `api/` and `web/` packages and moved FastAPI callbacks to `/api/fastapi`.
- Moved FastAPI DTOs into `dto/fastapi` and integration classes into `integration/`.
- Updated security matchers and FastAPI secret filter to align with `/api/fastapi`.

### [0.5.1] - 2026-03-20

User profile and shelf web features stabilized.

#### Added

- Web controllers for home, bookshelf, settings, auth, and user profile pages.

#### Changed

- User profile API endpoints moved under `/api`.

### [0.5.0] - 2026-03-19

Kafka flow and book-level results.

#### Added

- Book fields for aggregation: `chaptersCount`, `nerCompletedCount`, `characters`, `findPairsResult`, `relationsResult`.
- Book-level callbacks for find-pairs and relations.

#### Changed

- Chapter analysis and NER are triggered automatically via Kafka during chapter upload.
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
