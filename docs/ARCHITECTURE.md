# Architecture — StoryShelf (MVP)

## Tech Stack

| Warstwa   | Technologia |
|-----------|-------------|
| Frontend  | SvelteKit 2 + Svelte 5 + Tailwind v4 + TypeScript (Node adapter) |
| Backend   | Django 6 + Django REST Framework + Python 3.13 |
| Auth      | JWT — access token w pamięci, refresh token w HttpOnly cookie (djangorestframework-simplejwt) |
| Baza      | PostgreSQL 16 |
| Infra     | Docker Compose (dev + prod), Caddy reverse proxy |
| CI/CD     | GitHub Actions — lint, testy, docker build |

## Kontenery

```
svelte (:5174 dev, :3000 prod) → django (:8000) → db (PostgreSQL :5432)
```

3 kontenery, bez workera/brokera kolejkowego (M1–M5 synchroniczne).

## Auth flow

1. Login → `POST /api/auth/login/` → access token (body) + refresh token (HttpOnly cookie)
2. Access token w singletonie w pamięci przeglądarki, nigdy w localStorage
3. SvelteKit `handleFetch` forwarduje cookies przy SSR
4. 401 → `POST /api/auth/refresh/` → nowy access token
5. Logout → blacklist refresh token w PostgreSQL

Patrz [ADR-001](decisions/ADR-001-jwt-httponly-cookies.md).

## Django apps

| App       | Odpowiedzialność |
|-----------|------------------|
| `users/`  | Custom User (email, handle, display_name, bio, avatar_url, profile_public), auth, profil, follow, data export |
| `books/`  | Book CRUD, nested M2M (Author/Genre/Tag przez through-modele), Serie FK, slug, avg_rating; import z Google Books (`import_books` management command) |
| `library/`| Read-only API — Author, Serie, Genre, Tag (publiczne) |
| `ratings/`| Rating (PUT-upsert), sygnał przelicza `Book.avg_rating`/`ratings_count` |
| `shelf/`  | ShelfEntry (status czytania, current_page) + custom półki (Shelf + ShelfMembership), publiczny odczyt bramkowany `profile_public` |
| `reviews/`| Review (body, unique user+book, PUT-upsert, publiczna lista, owner-only delete, `author_rating`) |
| `config/` | Settings (dev/prod split), urls, pagination |

## Model relations

```
User
 ├── UserFollow (follower/following)
 ├── Rating (user+book, unique)
 ├── ShelfEntry (user+book, status, current_page)
 ├── Shelf (owner) ── ShelfMembership ── Book
 └── Review (user+book, unique)
Book (title, slug, year, isbn, description, page_count, cover_url, avg_rating)
 ├── serie → FK Serie (nullable)
 ├── Author (M2M through BookAuthor)
 ├── Genre (M2M through BookGenre)
 └── Tag (M2M through BookTag)
```

## API surface (M1–M5)

```
/api/auth/            register, login, refresh, logout
/api/users/me/        profil, settings (profile_public), email, password, avatar, export
/api/u/{handle}/      publiczny profil
/api/u/{handle}/shelves/   publiczne custom półki (bramkowane profile_public)
/api/authors/, /api/genres/, /api/series/, /api/tags/   (read-only)
/api/books/           lista, szczegóły (slug), filtry/search/sort
/api/ratings/         PUT-upsert oceny (+ /api/ratings/{id}/)
/api/shelf/entries/   ShelfEntry (status czytania, current_page)
/api/shelves/         custom półki (owner CRUD) + add/remove książek
/api/reviews/, /api/reviews/me/, /api/reviews/{id}/   recenzje
/api/schema/, /api/docs/
```

> Książki dodaje się przez Django admin, `BookWriteSerializer` (admin-only) lub `manage.py import_books <isbn>` (Google Books).

## Testy

- Backend: `DJANGO_ENV=dev uv run python manage.py test` (Django TestCase + DRF APITestCase)
- Kontrakt API: `config/tests/test_openapi_schema.py` vs `docs/api/openapi.yml` (`make regenerate-openapi` po zmianie API)
- Frontend: `npm run check` (svelte-check), `npm run lint` (ESLint + Prettier)
- E2E: `npx playwright test` (seed przez API w `global-setup.ts`)
