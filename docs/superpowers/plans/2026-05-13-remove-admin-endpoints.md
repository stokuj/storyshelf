# Remove Admin API Endpoints and User.Role Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove all admin-only API endpoints, remove `User.role` field, and add own-review deletion. Admin moves to Django Admin panel exclusively.

**Architecture:** Mechanical removal — delete write methods from views, remove permission classes, simplify views to GET-only where applicable. `Book` and `Library` views drop to plain `ListAPIView` + `RetrieveAPIView`. `ReviewDeleteView` gains owner check. `User.role` field removed with migration.

**Tech Stack:** Django 6, DRF, Django test runner, Ruff

---

## File Structure

- Modify: `backend-django/users/models.py` — remove `Role` TextChoices and `role` field
- Modify: `backend-django/books/views.py` — remove `IsAdmin`, simplify views to GET-only
- Modify: `backend-django/books/urls.py` — update imports to renamed views
- Modify: `backend-django/library/views.py` — remove `IsAdminOrReadOnly`, simplify views
- Modify: `backend-django/library/urls/authors.py` — update imports
- Modify: `backend-django/library/urls/series.py` — update imports
- Modify: `backend-django/library/urls/genres.py` — update imports
- Modify: `backend-django/reviews/views.py` — remove `IsAdminForDelete`, add owner check
- Modify: `backend-django/config/test_helpers.py` — remove `cls.admin`
- Modify: `backend-django/books/tests/test_books.py` — remove admin POST/PUT/DELETE tests
- Modify: `backend-django/reviews/tests/test_views.py` — replace admin-delete tests with owner-delete tests
- Modify: `backend-django/library/tests/test_views.py` — remove admin write tests
- Modify: `backend-django/shelf/tests/test_views.py` — remove admin references
- Create: `backend-django/users/migrations/0004_remove_user_role.py` — auto-migration

### Task 1: Remove User.role field and generate migration

**Files:**
- Modify: `backend-django/users/models.py:26-32`

- [ ] **Step 1: Remove Role TextChoices and role field**

Replace lines 26-32 of `backend-django/users/models.py`:

```python
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=30, unique=True)
    bio = models.TextField(max_length=500, blank=True, default="")
    avatar_url = models.URLField(blank=True, default="")
    profile_public = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
```

Removes `class Role` (lines 26-28) and `role` field (line 32). All other fields unchanged.

- [ ] **Step 2: Generate the auto-migration**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py makemigrations users --name remove_user_role`

Expected: Creates `backend-django/users/migrations/0004_remove_user_role.py` with `RemoveField` for `role`.

- [ ] **Step 3: Apply migration**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py migrate`

Expected: `Applying users.0004_remove_user_role... OK`

- [ ] **Step 4: Commit**

```bash
git add backend-django/users/models.py backend-django/users/migrations/0004_remove_user_role.py
git commit -m "refactor: remove User.role field"
```

### Task 2: Simplify books/views.py — remove IsAdmin, make views GET-only

**Files:**
- Modify: `backend-django/books/views.py`

- [ ] **Step 1: Remove IsAdmin class (lines 20-22)**

Delete:
```python
class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "ADMIN"
```

- [ ] **Step 2: Rename BookListCreateView → BookListView, remove POST support**

Replace lines 25-60. Current class handles `GET` and `POST`. New class is `GET`-only `ListAPIView`:

```python
class BookListView(generics.ListAPIView):
    serializer_class = BookListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        qs = Book.objects.select_related("serie").prefetch_related("authors", "tags", "genres")
        q = self.request.query_params.get("q", "")
        if q:
            q_lower = q.lower()
            qs = qs.filter(
                Q(title__icontains=q_lower)
                | Q(bookauthor__author__name__icontains=q_lower)
                | Q(genres__name__icontains=q_lower)
            ).distinct()
        return qs
```

- [ ] **Step 3: Rename BookDetailView → BookRetrieveView, remove write support**

Replace lines 63-85. Current class handles `GET`, `PUT`, `PATCH`, `DELETE`. New class is `GET`-only `RetrieveAPIView`:

```python
class BookRetrieveView(generics.RetrieveAPIView):
    serializer_class = BookDetailSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Book.objects.prefetch_related(
            Prefetch("chapters", queryset=Chapter.objects.order_by("chapter_number")),
            Prefetch(
                "character_relationships",
                queryset=CharacterRelationship.objects.select_related(
                    "from_character", "to_character"
                ),
            ),
            Prefetch("reviews"),
            "authors",
            "tags",
            "genres",
        )
```

- [ ] **Step 4: Simplify ChapterView — remove post() and delete()**

Replace lines 88-131. Keep only `get()`:

```python
class ChapterView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, book_id):
        chapters = Chapter.objects.filter(book_id=book_id).order_by("chapter_number")
        return Response(ChapterSerializer(chapters, many=True).data)
```

- [ ] **Step 5: Clean up unused imports**

Remove `get_object_or_404` from imports (no longer needed in this file after removing `post()` and `delete()`). Remove `status` from import (only used in removed methods). Remove `BookCreateSerializer` from serializer imports (no longer used).

Updated imports:
```python
from django.db.models import Prefetch, Q
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Book, Chapter
from analysis.models import BookCharacter, CharacterRelationship
from .serializers import (
    BookListSerializer,
    BookDetailSerializer,
    ChapterSerializer,
    BookCharacterSerializer,
    CharacterRelationSerializer,
)
```

- [ ] **Step 6: Commit**

```bash
git add backend-django/books/views.py
git commit -m "refactor: remove admin write endpoints from books views"
```

### Task 3: Update books/urls.py and remove unused import from library views

**Files:**
- Modify: `backend-django/books/urls.py`

- [ ] **Step 1: Update books/urls.py imports**

Replace the file content:

```python
from django.urls import path
from .views import (
    BookListView,
    BookRetrieveView,
    ChapterView,
    BookCharactersView,
    BookRelationsView,
)
from reviews.views import BookReviewListCreateView

urlpatterns = [
    path("", BookListView.as_view()),
    path("<int:pk>/", BookRetrieveView.as_view()),
    path("<int:pk>/reviews/", BookReviewListCreateView.as_view()),
    path("<int:book_id>/chapters/", ChapterView.as_view()),
    path("<int:book_id>/characters/", BookCharactersView.as_view()),
    path("<int:book_id>/relations/", BookRelationsView.as_view()),
]
```

- [ ] **Step 2: Commit**

```bash
git add backend-django/books/urls.py
git commit -m "refactor: update books URLs to renamed GET-only views"
```

### Task 4: Simplify library/views.py and update library URLs

**Files:**
- Modify: `backend-django/library/views.py`
- Modify: `backend-django/library/urls/authors.py`
- Modify: `backend-django/library/urls/series.py`
- Modify: `backend-django/library/urls/genres.py`

- [ ] **Step 1: Rewrite library/views.py — remove IsAdminOrReadOnly, simplify views**

Replace the entire file:

```python
from rest_framework import generics, permissions

from .models import Author, Genre, Serie
from .serializers import AuthorSerializer, GenreSerializer, SeriesSerializer


class AuthorListView(generics.ListAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class AuthorRetrieveView(generics.RetrieveAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [permissions.AllowAny]


class SeriesListView(generics.ListAPIView):
    queryset = Serie.objects.all()
    serializer_class = SeriesSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class SeriesRetrieveView(generics.RetrieveAPIView):
    queryset = Serie.objects.all()
    serializer_class = SeriesSerializer
    permission_classes = [permissions.AllowAny]


class GenreListView(generics.ListAPIView):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class GenreRetrieveView(generics.RetrieveAPIView):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [permissions.AllowAny]
```

- [ ] **Step 2: Update library/urls/authors.py**

```python
from django.urls import path
from library.views import AuthorListView, AuthorRetrieveView

urlpatterns = [
    path("", AuthorListView.as_view()),
    path("<int:pk>/", AuthorRetrieveView.as_view()),
]
```

- [ ] **Step 3: Update library/urls/series.py**

```python
from django.urls import path
from library.views import SeriesListView, SeriesRetrieveView

urlpatterns = [
    path("", SeriesListView.as_view()),
    path("<int:pk>/", SeriesRetrieveView.as_view()),
]
```

- [ ] **Step 4: Update library/urls/genres.py**

```python
from django.urls import path
from library.views import GenreListView, GenreRetrieveView

urlpatterns = [
    path("", GenreListView.as_view()),
    path("<int:pk>/", GenreRetrieveView.as_view()),
]
```

- [ ] **Step 5: Commit**

```bash
git add backend-django/library/views.py backend-django/library/urls/authors.py backend-django/library/urls/series.py backend-django/library/urls/genres.py
git commit -m "refactor: remove admin write endpoints from library views"
```

### Task 5: Update reviews/views.py — owner-based delete

**Files:**
- Modify: `backend-django/reviews/views.py`

- [ ] **Step 1: Remove IsAdminForDelete, add owner check to ReviewDeleteView**

Replace the entire file:

```python
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from books.models import Book

from .models import Review
from .serializers import ReviewSerializer


class BookReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    pagination_class = None

    def get_queryset(self):
        return (
            Review.objects.filter(book_id=self.kwargs["pk"])
            .select_related("user", "book")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        book = get_object_or_404(Book, id=self.kwargs["pk"])
        serializer.save(user=self.request.user, book=book)


class ReviewDeleteView(generics.DestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj = super().get_object()
        if obj.user != self.request.user:
            raise PermissionDenied("You can only delete your own reviews.")
        return obj
```

- [ ] **Step 2: Commit**

```bash
git add backend-django/reviews/views.py
git commit -m "feat: allow users to delete their own reviews, remove admin delete"
```

### Task 6: Update tests and test_helpers

**Files:**
- Modify: `backend-django/config/test_helpers.py`
- Modify: `backend-django/books/tests/test_books.py`
- Modify: `backend-django/reviews/tests/test_views.py`
- Modify: `backend-django/library/tests/test_views.py`
- Modify: `backend-django/shelf/tests/test_views.py`

- [ ] **Step 1: Remove cls.admin from test_helpers**

Replace `backend-django/config/test_helpers.py`:

```python
from users.models import User


class AuthTestHelper:
    """Mixin that creates test users."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="user@test.com",
            username="testuser",
            password="password123",
        )
```

- [ ] **Step 2: Update books/tests/test_books.py**

Remove all admin-only POST/PUT/DELETE tests. The file should keep only GET tests. Remove these test methods and classes:

Remove from `BookListTest`:
- `test_post_create_book_as_admin_returns_201`
- `test_post_create_book_as_user_returns_403`
- `test_post_create_book_unauthenticated_returns_401`
- `test_post_create_book_missing_author_returns_400`
- `test_post_create_book_nonexistent_author_returns_404`

Remove `BookDetailTest` entirely (lines 97-156, contains `test_put_update_book_as_admin_returns_200`, `test_delete_book_as_admin_returns_204`).

Remove `ChapterTest` entirely (lines 159-241, contains `test_post_upload_chapters_as_admin_returns_201`, `test_delete_chapters_as_admin_returns_204`, `test_post_upload_empty_file_as_admin_returns_400`, `test_post_upload_as_user_returns_403`).

After cleanup, rename `BookListTest` to `BookListViewTest`.

- [ ] **Step 3: Update reviews/tests/test_views.py**

In `ReviewDeleteTest`:
- Remove `test_delete_review_as_admin_returns_204`
- Remove `test_delete_review_as_regular_user_returns_403`
- Add:

```python
def test_delete_own_review_returns_204(self):
    self.client.force_authenticate(user=self.user)
    resp = self.client.delete(f"/api/reviews/{self.review.id}/")
    self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
    self.assertFalse(Review.objects.filter(id=self.review.id).exists())

def test_delete_other_users_review_returns_403(self):
    other = User.objects.create_user(
        email="other@test.com", username="otheruser", password="password123"
    )
    other_review = Review.objects.create(
        user=other, book=self.book, rating=3, content="Other"
    )
    self.client.force_authenticate(user=self.user)
    resp = self.client.delete(f"/api/reviews/{other_review.id}/")
    self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
```

Add import at top of file: `from users.models import User`

- [ ] **Step 4: Update library/tests/test_views.py**

Remove all admin POST/PUT/DELETE tests. Keep only GET tests.

In `AuthorListCreateTest` (rename to `AuthorListTest`): remove `test_post_create_author_as_admin_returns_201`, `test_post_create_author_as_user_returns_403`, `test_post_create_author_unauthenticated_returns_401`, `test_post_create_author_missing_name_returns_400`.

In `AuthorDetailTest` (rename to `AuthorRetrieveTest`): remove `test_put_update_as_admin_returns_200`, `test_delete_as_admin_returns_204`.

Remove `Series*Test` admin-write tests similarly.

- [ ] **Step 5: Update shelf/tests/test_views.py**

Replace remaining `self.admin` references with `self.user` (after test_helpers removes admin, any shelf test using admin needs to use user instead).

- [ ] **Step 6: Run all tests**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test`

Expected: All remaining tests pass. Test count will decrease from 115 because admin-only tests are removed.

- [ ] **Step 7: Commit**

```bash
git add backend-django/config/test_helpers.py backend-django/books/tests/test_books.py backend-django/reviews/tests/test_views.py backend-django/library/tests/test_views.py backend-django/shelf/tests/test_views.py
git commit -m "test: remove admin-only tests, add owner review-delete tests"
```

### Task 7: Lint and final verification

**Files:**
- None new

- [ ] **Step 1: Run Ruff lint**

Run: `cd backend-django && uv run ruff check .`

Expected: No new errors from our changes. Pre-existing issues only.

- [ ] **Step 2: Run full test suite**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test`

Expected: All tests pass.

- [ ] **Step 3: Check for pending migrations**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py makemigrations --check --dry-run`

Expected: `No changes detected`

- [ ] **Step 4: Commit (if lint fixes needed)**

```bash
git add backend-django/
git commit -m "chore: post-refactor lint and final verification"
```
