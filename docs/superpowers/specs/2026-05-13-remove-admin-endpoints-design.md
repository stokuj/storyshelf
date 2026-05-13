# Remove Admin API Endpoints and User.Role — Design

This spec defines the removal of all admin-only API endpoints and the `User.role` field,
leaving a two-role frontend: guest (unauthenticated) and user (authenticated). Admin
operations move exclusively to the Django Admin panel.

**Attention Conservation Notice**
For: Developer implementing the change
What: Design for stripping admin-only API surfaces, simplifying User model, and keeping own-review deletion
Action: Review each section, confirm the endpoint shape, then approve for implementation
Skip if: You already agreed to the final endpoint list during grilling

## What We Need From You

Review and approve this spec before implementation starts.

## Background

After removing the MODERATOR role, the only remaining role was ADMIN. All write
operations on books, authors, series, genres, and chapters were gated behind
`role == "ADMIN"`. The decision is to remove these API surfaces entirely and
handle admin operations through the Django Admin panel (`/admin/`).

Additionally, the `User.role` field with a single remaining value (`USER`) is
removed from the model. The Django Admin panel uses `is_staff` and `is_superuser`,
not `role`.

## Architecture

Three categories of change:

1. **Remove endpoints** — delete `POST/PATCH/PUT/DELETE` methods on admin-gated views
2. **Rename views** — change class names from `*Create*`/`*Destroy*` to reflect their
   remaining GET-only behavior
3. **Simplify permissions** — remove `IsAdmin`, `IsAdminOrReadOnly`, `IsAdminForDelete`
   classes; replace with `IsAuthenticated` or `AllowAny` as appropriate
4. **User model cleanup** — remove `role` field and `Role` TextChoices from `User`
5. **Own-review deletion** — `ReviewDeleteView` checks `review.user == request.user`
   instead of admin role

## Final Endpoint Shape

### Auth (no changes)
| Endpoint | Methods |
|---|---|
| `/api/auth/register/` | POST |
| `/api/auth/login/` | POST |
| `/api/auth/refresh/` | POST |
| `/api/auth/logout/` | POST |
| `/api/auth/me/` | GET |

### Users (no changes)
| Endpoint | Methods |
|---|---|
| `/api/users/me/` | GET, PATCH, PUT |
| `/api/users/me/visibility/` | PATCH |
| `/api/users/{username}/` | GET |
| `/api/users/{username}/follow/` | POST, DELETE |
| `/api/users/{username}/followers/` | GET |
| `/api/users/{username}/following/` | GET |

### Books (write methods removed)
| Endpoint | Methods |
|---|---|
| `/api/books/` | GET |
| `/api/books/{id}/` | GET |
| `/api/books/{id}/reviews/` | GET, POST |
| `/api/books/{id}/chapters/` | GET |
| `/api/books/{id}/characters/` | GET |
| `/api/books/{id}/relations/` | GET |

### Reviews (admin DELETE removed, own-review delete added)
| Endpoint | Methods |
|---|---|
| `/api/reviews/{id}/` | DELETE (owner only) |

### Shelf (no changes)
| Endpoint | Methods |
|---|---|
| `/api/shelf/` | GET |
| `/api/shelf/{bookId}/` | GET, POST, PATCH, DELETE |

### Library (write methods removed)
| Endpoint | Methods |
|---|---|
| `/api/authors/` | GET |
| `/api/authors/{id}/` | GET |
| `/api/series/` | GET |
| `/api/series/{id}/` | GET |
| `/api/genres/` | GET |
| `/api/genres/{id}/` | GET |

### Schema (no changes)
| Endpoint | Methods |
|---|---|
| `/api/schema/` | GET |
| `/api/docs/` | GET |

## File Changes

### `backend-django/users/models.py`
Remove `class Role` TextChoices and the `role` field from `User`.

### `backend-django/books/views.py`
- Remove `IsAdmin` class.
- `BookListCreateView` → `BookListView` — `ListAPIView`, `permission_classes = [AllowAny]`.
- `BookDetailView` → `BookRetrieveView` — `RetrieveAPIView`, `permission_classes = [AllowAny]`.
- `ChapterView` — remove `post()` and `delete()` methods. Keep `get()` only.
- `BookCharactersView` — no changes.
- `BookRelationsView` — no changes.

### `backend-django/books/urls.py`
- Remove the duplicate `/books/{id}/details/` path if present.
- Remove paths only using removed views. Keep GET-only registrations.

### `backend-django/library/views.py`
- Remove `IsAdminOrReadOnly` class.
- `AuthorListCreateView` → `AuthorListView` — `ListAPIView`, `AllowAny`.
- `AuthorRetrieveUpdateDestroyView` → `AuthorRetrieveView` — `RetrieveAPIView`, `AllowAny`.
- Same pattern for `Series*` and `Genre*` views.

### `backend-django/library/urls/*.py`
- `authors.py` — only `ListAPIView` + `RetrieveAPIView`.
- `series.py` — same.
- `genres.py` — same.

### `backend-django/reviews/views.py`
- Remove `IsAdminForDelete` class.
- `ReviewDeleteView` — `permission_classes = [IsAuthenticated]`.
- Override `get_object()` to check `obj.user == request.user`.

### `backend-django/config/test_helpers.py`
- Remove `cls.admin`. Only `cls.user` remains.

### Test files
- Remove tests for removed endpoints.
- Remove tests that authenticated as admin.
- Add test: user can delete own review.
- Add test: user cannot delete another user's review.
- Update test names and references where `as_admin` no longer applies.

### Migrations
- New migration: `AlterField` or `RemoveField` for the `role` column on `User`.

## Key Decisions

| Decision | Rationale |
|---|---|
| Remove `role` field entirely | Single value = no information. `is_staff`/`is_superuser` serve Django Admin. |
| Keep `ReviewDeleteView` with owner check | Standard UX: users delete their own content. |
| Remove rather than hide admin endpoints | Dead endpoints are tech debt. Django Admin covers the use case. |
| Rename views to match remaining behavior | Avoids confusion: `*Create*` without Create is misleading. |
