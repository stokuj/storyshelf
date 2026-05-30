Celem projektu jest stwożenie aplikacji przypominającej goodreads/lubimiczytrać. Tracker książek + Fukcje AI potem dodane. Rozbudowa fazami/milestonami.

Django RESTframework, svelte, docker.
Na sam początek bez żadnego celery, flower, cenie minimalizm i powolne dodowanie fukcje/docmen/prosty kod. Ma działąć być poprawne bez zbędnej abstarakcji/interaceu.

Na ten moment powinny być 2 domeny:
- user czyli logowanie, rejestracji, autoryzacja czyli jakis tam token. Profile usera/ panel settings, profil prywatny/publiczny.
- Domena książek: strona /discovery. Czyli dodawanie ksiązek, user moge sledzic ksiażki
  
Udało mi się odsyskac roadmape chyba (PYTAJ!):
The project is StoryShelf, a book-tracking app. The roadmap uses a milestone-based approach:
M1 (✅ completed): Auth and user profile. 5 phases (1a-1f). User can register, login, manage profile/settings, see public profile. ~94 backend tests, svelte-check 0 errors, 37 Playwright tests.
M2: Book catalog. 5 phases (2a-2e). User can browse, search, and filter books; see details (authors, genres, description, rating).
- 2a: Library CRUD API (Author, Serie, Genre, Tag — 4 models, ReadOnlyModelViewSet, public)
- 2b: Book CRUD API + seed (Book model with nested M2M, filters, search, sort, seed_books command with 20 books from fixture)
- 2c: /discover page (SSR + client-side fetch, grid, search with debounce 300ms, filters, pagination 12/page)
- 2d: /books/slug page (2-column desktop / single-column mobile, cover, meta, description, 404 error page)
- 2e: E2E Playwright tests for discover and book detail (13 tests)
M3: Reading statuses and ratings. 5 phases (3a-3e). User can mark reading status (Want to Read/Reading/Read), track page progress, rate books (1-5 stars affecting community average).
- 3a: Rating API (new ratings/ app, PUT as upsert, signal for avg_rating)
- 3b: ShelfEntry CRUD API (remove personal_rating, add current_page with validation)
- 3c: /shelf frontend (3 tabs with client-side filtering, ShelfBookCard with inline actions)
- 3d: E2E for shelf
- 3e: RatingWidget on /books/slug page
M4: Reviews. 3 phases (4a-4c). User can write reviews, see others' reviews and rating distribution.
- 4a: Review CRUD API (review content only, rating from separate model, chronological ordering)
- 4b: Reviews section on /books/slug (RatingSummary, ReviewForm, ReviewCard, pagination)
- 4c: E2E for reviews (9 tests)
M5: Custom shelves (collections). User can create own collections, manage book order, share publicly.
- 5a: Shelf + ShelfMembership CRUD API
- 5b: Frontend — list, CRUD, AddToShelfModal, public view /u/handle/shelves/slug
- 5c: E2E
Pipeline: brainstorming → Spec → Plan → Kod → Merge (5 steps, shortened from 8)
Gate: all phases in a milestone must have Spec + Plan before starting implementation.
"Czego nie robimy": No AI/LLM (deferred to post-MVP), no live Google Books import, no CSV/Goodreads import, no Celery/Redis/RabbitMQ, no real-time collaboration, no native mobile, no subscriptions.
Dependencies: M1 → M2 → M3 → M4 → M5 (sequential). M3 3a depends on Book model from M2 2b. M3 3e depends on M2 2d frontend.
I think that's the main content. Let me present it clearly.
Z pamięci:
Roadmapa StoryShelf (MVP)
5 milestone'ów, sekwencyjne zależności: M1 → M2 → M3 → M4 → M5
M	Cel	Fazy	Status
M1	Auth + profil	1a–1f	✅
M2	Katalog książek	2a–2e	pending
M3	Statusy czytania + oceny	3a–3e	pending
M4	Recenzje	4a–4c	pending
M5	Własne półki (kolekcje)	5a–5c	pending
M2 — Katalog książek (5 faz)
Faza	Co
2a	Library CRUD API — 4 modele (Author, Serie, Genre, Tag), ReadOnlyModelViewSet, publiczne
2b	Book CRUD API + seed — nested M2M przez nazwy, filtry/search/sort, fixture JSON 20 książek
2c	/discover — grid BookCard, search z debounce 300ms, filtry, paginacja 12/s, SSR + client fetch
2d	/books/[slug] — 2-kolumnowy layout, cover, meta, autorzy jako linki, opis, +error.svelte
2e	E2E Playwright — discover (7 testów) + book-detail (6 testów)
M3 — Statusy + Oceny (5 faz)
Faza	Co
3a	Rating API — nowa app ratings/, PUT upsert, sygnał aktualizujący Book.avg_rating
3b	ShelfEntry CRUD — +current_page, -personal_rating, user_rating przez Subquery
3c	/shelf frontend — 3 zakładki, ShelfBookCard z akcjami inline, auth guard
3d	E2E shelf — 7 testów
3e	RatingWidget na /books/[slug] — interaktywne gwiazdki, auth-conditional
M4 — Recenzje (3 fazy)
Faza	Co
4a	Review CRUD API — tylko content (10-2000 znaków), author_rating przez Subquery, chronologicznie
4b	Sekcja recenzji na /books/[slug] — RatingSummary, ReviewForm, ReviewCard, "Załaduj więcej"
4c	E2E reviews — 9 testów
M5 — Własne półki (3 fazy)
Faza	Co
5a	Shelf + ShelfMembership CRUD API — user-scoped, public/private, kolejność
5b	Frontend — CRUD półek, AddToShelfModal, publiczny widok /u/[handle]/shelves/[slug]
5c	E2E
Pipeline: brainstorming → Spec → Plan → Kod → Merge (5 kroków)
Gate: wszystkie fazy milestone'a muszą mieć Spec + Plan przed startem implementacji.
Czego nie robimy: AI/LLM, live Google Books import, CSV/Goodreads import, Celery/Redis/RabbitMQ, real-time collaboration, native mobile, subskrypcje.

teraz miej wiecej taka architekrua na ten moment:
Architecture — StoryShelf (MVP)
Tech stack
Warstwa	Technologia
Frontend	SvelteKit 2 + Svelte 5 + Tailwind v4 + TypeScript (Node adapter)
Backend	Django 6 + Django REST Framework + Python 3.12
Auth	JWT — access token w pamięci, refresh token w HttpOnly cookie (djangorestframework-simplejwt)
Baza	PostgreSQL 16
Infra	Docker Compose (dev + prod), Caddy reverse proxy
CI/CD	GitHub Actions — lint, testy, docker build
Kontenery
svelte (:5174 dev, :3000 prod) → django (:8000) → db (PostgreSQL :5432)
3 kontenery, bez workera/brokera kolejkowego (M1-M5 synchroniczne).
Auth flow
1. Login → POST /api/auth/login/ → access token (body) + refresh token (HttpOnly cookie)
2. Access w singletonie w pamięci przeglądarki, nigdy w localStorage
3. SvelteKit handleFetch forwarduje cookies na SSR
4. 401 → POST /api/auth/refresh/ → nowy access token
5. Logout → blacklist refresh token w PostgreSQL
Django apps
App	Odpowiedzialność
users/	Custom User (email, handle, display_name, bio, avatar_url, profile_public), auth endpointy, profile
books/	Book CRUD, nested M2M (Author, Genre, Tag przez through-modele), Serie FK, slug, avg_rating
library/	Read-only API — Author, Serie, Genre, Tag (publiczne)
shelf/	ShelfEntry (status, current_page, start/finish_date), Shelf + ShelfMembership (M5)
ratings/	Rating (user+book, 1-5), sygnał → Book.avg_rating
reviews/	Review (content 10-2000 znaków, created_at, updated_at), author_rating przez Subquery
config/	Settings (dev/prod split), urls, pagination
Model relations
User
 ├── ShelfEntry (status, current_page) → Book
 ├── Review (content) → Book
 └── Rating (1-5) → Book
Book (title, slug, year, isbn, description, page_count, cover_url, avg_rating, ratings_count)
 ├── serie → FK Serie (nullable)
 ├── Author (M2M through BookAuthor)
 ├── Genre (M2M through BookGenre)
 └── Tag (M2M through BookTag)
- avg_rating / ratings_count na Book aktualizowane sygnałem post_save/post_delete z ratings.Rating
- unique(user, book) na ShelfEntry, Review, Rating — jeden wpis per user per książka
API surface (po M4)
Prefix
/api/auth/
/api/users/me/
/api/u/{handle}/
/api/authors/, /api/genres/, /api/series/, /api/tags/
/api/books/
/api/ratings/
/api/shelf/entries/
/api/reviews/
/api/schema/
/api/docs/
Frontend routes (po M4)
Route	Auth
/	Nie
/login	Nie
/signup	Nie
/settings/*	Tak
/u/{handle}	Nie
/discover	Nie
/books/[slug]	Nie
/shelf	Tak
E2E
- Playwright w svelte-frontend/e2e/
- global-setup.ts seeduje dane przez API
- Storage state w .auth/*.json (gitignored)
- Per milestone: auth.spec.ts → discover.spec.ts + book-detail.spec.ts → shelf-status.spec.ts → reviews.spec.ts
Testy
- Backend: DJANGO_ENV=dev uv run python manage.py test (Django TestCase + DRF APITestCase)
- Frontend: npm run check (svelte-check), npm run lint (ESLint)
- E2E: npx playwright test
- Łącznie: ~94 backend + ~37 E2E na M1, rosnąco per milestone
  
  DECYJE-> TO TRZEBA jakos zapisac zbiorczo najwazniejsze do decisions jezeli są kliczowe:
  M2
 1. cover_url jako URLField(max_length=500, blank=True) na Book
 2. Nested M2M (author/genre/tag) przez nazwę — case-insensitive, .strip(), get_or_create, PATCH = full replace
 3. Normalizacja: authors → .strip().title(), genres/tags → .strip().lower()
 4. Seed: fixture JSON 20 książek, loaddata, idempotentne, zero zależności sieciowych
 5. Library CRUD — ReadOnlyModelViewSet, GET publiczny, modyfikacje tylko przez Django admin
 6. Filtry /api/books/ — manualne query params: search, author, genre, year_min, year_max, ordering. Bez django-filter
 7. Paginacja — StandardPagination, page_size=12 dla books
 8. Katalog publiczny — /discover i /books/[slug] bez auth guarda
 9. Pozycja w serii — nested serie w BookSerializer, frontend: {serie.name} #{position_in_series}
10. E2E seed — przez API w global-setup.ts, admin login przed POST
M3
 11. Spec + plan M3 równolegle z implementacją M2
 12. current_page na ShelfEntry — IntegerField(null=True, blank=True), walidacja ≤ book.page_count w clean(), bez auto-modyfikacji
 13. personal_rating na ShelfEntry — usunięty
 14. Rating jako osobny model — Rating(user, book, rating 1-5), unique(user, book), nowa app ratings/
 15. Sygnał ratings/signals.py — post_save/post_delete → select_for_update + transaction.atomic → aktualizuje Book.avg_rating i ratings_count
 16. Stary sygnał reviews/signals.py — usunięty
 17. Rating w M3, nie czeka na M4
 18. Rating API — /api/ratings/, PUT jako upsert (update_or_create), 201 dla create, 200 dla update
 19. ShelfEntry endpoint — /api/shelf/entries/, nie koliduje z M5 custom shelves
20. ShelfEntry identyfikacja — przez book_slug w body, nie book ID
21. ShelfEntry response — nested book z pełnymi danymi (slug, title, cover_url, authors, genres, avg_rating, page_count)
22. user_rating inline — ShelfEntry serializer dorzuca rating usera przez Subquery annotację z ratings.Rating
23. Przejścia statusów — dowolne, bez walidacji backendowej
24. StatusDropdown + RatingWidget — akcje inline na ShelfBookCard, bez modala
25. RatingWidget lokalizacje — ShelfBookCard na /shelf + strona /books/[slug] (faza 3e)
26. 5 faz M3: 3a → 3b → 3c → 3d → 3e
27. /shelf filtrowanie — jedno zapytanie GET /api/shelf/entries/, client-side filter po statusie
28. /shelf bez paginacji — pełna lista (max kilkaset wpisów)
29. /shelf auth guard — +layout.server.ts SSR, redirect do /login
30. DELETE ShelfEntry — tak, DELETE /api/shelf/entries/{id}/
31. django-filter — wchodzi z M2, dostępne dla M3
32. Review (M4) — tylko tekst, bez pola rating. Wyświetla rating z ratings.Rating jeśli istnieje
33. Sygnał reviews/signals.py — usunięty w M3
M4
 34. Review bez pola rating — tylko content: TextField(max_length=2000), rating w ratings.Rating
 35. URL recenzji — /api/reviews/ top-level, ?book_slug=X wymagane
 36. Timestampy — created_at + updated_at, frontend wyświetla "Edytowano X temu"
 37. Paginacja — page_size=10
 38. Permissions — GET AllowAny, POST IsAuthenticated, PATCH/DELETE właściciel (IsOwnerOrReadOnly)
 39. author_rating — Subquery annotacja z ratings.Rating, jedno zapytanie
 40. 3 fazy M4 — sekwencyjnie
 41. RatingSummary — dane z Book (avg_rating, ratings_count) + agregacja Rating (client-side reduce), rozkład 1-5 jako słupki
 42. Własna recenzja — jeśli istnieje, ReviewForm zastąpiony ReviewCard z Edit/Delete inline
43. Empty states — niezalogowany: link do logowania, zalogowany: ReviewForm, brak recenzji: "Bądź pierwszy!"
44. Migracja Review — RemoveField rating + AddField updated_at
45. Walidacja content — MinLengthValidator(10) + max_length=2000
46. User dane w Review — UserPublicSerializer (handle, display_name, avatar_url), select_related("user")
47. Sortowanie recenzji — chronologiczne -created_at, najnowsze na górze, stabilne przy paginacji
48. Rozkład ocen — client-side z istniejącego GET /api/ratings/?book_slug=X, zero nowego backend kodu
49. Layout recenzji — RatingSummary → ReviewForm/własna karta → lista cudzych → "Załaduj więcej"
50. Edycja recenzji — inline, karta zamienia się w textarea z Zapisz/Anuluj
51. Delete recenzji — inline dwuetapowe, bez window.confirm()
52. book_slug wymagany w GET — brak → 400
53. Paginacja frontend — "Załaduj więcej", append do listy, spójne z /discover
54. Własna recenzja w liście — backend zwraca wszystkie, frontend filtruje swoją client-side i pokazuje na górze
55. E2E seed — global-setup.ts przez API, 2 userów z recenzjami i ratingami
56. ReviewCard truncation — 280 znaków + "Czytaj więcej" inline expand
57. RatingSummary wygląd — duża cyfra + readonly gwiazdki + słupki 1-5 z licznikami. Zero ocen: "Brak ocen"
58. Odwrócenie M3 Simplicity Cut 1 — przywrócono Subquery user_rating w ShelfEntry (zamiast client-side merge)
---
