# Phase 3a: Rating API — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** New ratings/ Django app with Rating model, PUT upsert API, signal updating Book.avg_rating.

**Architecture:** New Django app `ratings/`. Rating model (user FK, book FK, rating 1-5, unique(user,book)). ModelViewSet with upsert create(). post_save/post_delete signal → Book.avg_rating + ratings_count via select_for_update(). Remove old reviews/signals.py.

**Tech Stack:** Django 6, DRF, pytest (DJANGO_ENV=dev uv run python manage.py test ratings), uv, ruff.

---

## Task 1: Create ratings app skeleton

- [ ] Create directory `backend-django/ratings/` with `__init__.py`, `apps.py`, `tests/__init__.py`
- [ ] Register `"ratings"` in `INSTALLED_APPS` in `backend-django/config/settings/base.py`

### Files to create

#### `backend-django/ratings/__init__.py`
```python

```

#### `backend-django/ratings/apps.py`
```python
from django.apps import AppConfig


class RatingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ratings"

    def ready(self):
        import ratings.signals  # noqa
```

#### `backend-django/ratings/tests/__init__.py`
```python

```

### File to modify: `backend-django/config/settings/base.py`

In `INSTALLED_APPS` list, after `"shelf.apps.ShelfConfig",`, add:

```python
    "ratings.apps.RatingsConfig",
```

### Verify

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py check
# Expected: System check identified no issues (0 silenced).
```

### Commit

```bash
git add backend-django/ratings/ backend-django/config/settings/base.py
git commit -m "feat(ratings): scaffold ratings app with apps.py and settings registration"
```

---

## Task 2: Rating model + migration

- [ ] Create `backend-django/ratings/models.py` with Rating model
- [ ] Run `makemigrations ratings` and `migrate`

### File to create: `backend-django/ratings/models.py`

```python
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Rating(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ratings",
        db_index=True,
    )
    book = models.ForeignKey(
        "books.Book",
        on_delete=models.CASCADE,
        related_name="ratings",
        db_index=True,
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "book"], name="unique_user_book_rating"
            ),
        ]
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.handle} → {self.book.title} ({self.rating}/5)"
```

### Shell commands

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py makemigrations ratings
# Expected: Migrations for 'ratings': ratings/migrations/0001_initial.py ...

cd backend-django && DJANGO_ENV=dev uv run python manage.py migrate
# Expected: Applying ratings.0001_initial... OK
```

### Commit

```bash
git add backend-django/ratings/
git commit -m "feat(ratings): add Rating model with unique(user,book) constraint"
```

---

## Task 3: RatingSerializer

- [ ] Create `backend-django/ratings/serializers.py`

### File to create: `backend-django/ratings/serializers.py`

```python
from rest_framework import serializers

from books.models import Book

from .models import Rating


class RatingSerializer(serializers.ModelSerializer):
    book_slug = serializers.SlugRelatedField(
        slug_field="slug", queryset=Book.objects.all(), source="book"
    )

    class Meta:
        model = Rating
        fields = ["id", "book_slug", "rating"]
        read_only_fields = ["id"]
```

### Verify

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py shell -c "
from ratings.serializers import RatingSerializer
print(RatingSerializer)
"
# Expected: <class 'ratings.serializers.RatingSerializer'> (no errors)
```

### Commit

```bash
git add backend-django/ratings/serializers.py
git commit -m "feat(ratings): add RatingSerializer with SlugRelatedField for book_slug"
```

---

## Task 4: RatingViewSet

- [ ] Create `backend-django/ratings/views.py` with ModelViewSet

### File to create: `backend-django/ratings/views.py`

```python
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from books.models import Book

from .models import Rating
from .serializers import RatingSerializer


class RatingViewSet(viewsets.ModelViewSet):
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Rating.objects.filter(user=self.request.user).select_related("book")
        book_slug = self.request.query_params.get("book_slug")
        if book_slug:
            qs = qs.filter(book__slug=book_slug)
        return qs

    def create(self, request, *args, **kwargs):
        """Upsert: create or update rating for user+book pair. Returns 201 if created, 200 if updated."""
        book_slug = request.data.get("book_slug")
        try:
            book = Book.objects.get(slug=book_slug)
        except Book.DoesNotExist:
            return Response(
                {"book_slug": "Book not found."}, status=status.HTTP_404_NOT_FOUND
            )

        rating, created = Rating.objects.update_or_create(
            user=request.user,
            book=book,
            defaults={"rating": request.data.get("rating")},
        )
        serializer = self.get_serializer(rating)
        http_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=http_status)

    def perform_destroy(self, instance):
        instance.delete()
```

### Verify

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py check
# Expected: System check identified no issues (0 silenced).
```

### Commit

```bash
git add backend-django/ratings/views.py
git commit -m "feat(ratings): add RatingViewSet with PUT upsert and user-scoped queryset"
```

---

## Task 5: Signal + wire in apps.py

- [ ] Create `backend-django/ratings/signals.py`
- [ ] apps.py `ready()` already imports it (created in Task 1)

### File to create: `backend-django/ratings/signals.py`

```python
from django.db import transaction
from django.db.models import Avg, Count
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Rating


@receiver(post_save, sender=Rating)
@receiver(post_delete, sender=Rating)
def update_book_avg_rating(sender, instance, **kwargs):
    from books.models import Book

    with transaction.atomic():
        book = Book.objects.select_for_update().get(id=instance.book_id)
        result = Rating.objects.filter(book=book).aggregate(
            avg=Avg("rating"), count=Count("id")
        )
        book.avg_rating = round(result["avg"] or 0.0, 2)
        book.ratings_count = result["count"]
        book.save(update_fields=["avg_rating", "ratings_count"])
```

### Verify

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py check
# Expected: System check identified no issues (0 silenced).
```

### Commit

```bash
git add backend-django/ratings/signals.py
git commit -m "feat(ratings): add post_save/post_delete signal updating Book.avg_rating"
```

---

## Task 6: Remove reviews/signals.py

- [ ] Delete `backend-django/reviews/signals.py`
- [ ] Remove `import reviews.signals` from `backend-django/reviews/apps.py`

### File to delete

Delete: `backend-django/reviews/signals.py`

### File to modify: `backend-django/reviews/apps.py`

Change from:

```python
from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "reviews"

    def ready(self):
        import reviews.signals  # noqa
```

To:

```python
from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "reviews"
```

### Verify

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py check
# Expected: System check identified no issues (0 silenced).
```

### Commit

```bash
git rm backend-django/reviews/signals.py
git add backend-django/reviews/apps.py
git commit -m "refactor(reviews): remove reviews/signals.py — replaced by ratings/signals.py"
```

---

## Task 7: URL config

- [ ] Create `backend-django/ratings/urls.py` with DefaultRouter
- [ ] Add `path("api/", include("ratings.urls"))` to `backend-django/config/urls.py`

### File to create: `backend-django/ratings/urls.py`

```python
from rest_framework.routers import DefaultRouter

from .views import RatingViewSet

router = DefaultRouter()
router.register(r"ratings", RatingViewSet, basename="rating")
urlpatterns = router.urls
```

### File to modify: `backend-django/config/urls.py`

Add the include after the existing `api/` routes (e.g. after `path("api/u/", ...)`):

```python
    path("api/", include("ratings.urls")),
```

Full modified file should look like:

```python
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("users.urls.auth")),
    path("api/users/", include("users.urls.users")),
    path("api/u/", include("users.urls.public")),
    path("api/", include("ratings.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### Verify

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py check
# Expected: System check identified no issues (0 silenced).

cd backend-django && DJANGO_ENV=dev uv run python manage.py show_urls 2>/dev/null || uv run python -c "
from django.urls import get_resolver
resolver = get_resolver()
for url in resolver.url_patterns:
    print(url.pattern)
"
# Expected: api/ appears among url patterns
```

### Commit

```bash
git add backend-django/ratings/urls.py backend-django/config/urls.py
git commit -m "feat(ratings): add URL routing for /api/ratings/"
```

---

## Task 8: Test — CRUD (7 tests)

- [ ] Create `backend-django/ratings/tests/test_ratings.py`
- [ ] Write 7 CRUD tests: PUT create (201), PUT update (200), GET list, GET detail, GET list with book_slug filter (empty), DELETE (204), DELETE 404

### File to create: `backend-django/ratings/tests/test_ratings.py`

```python
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from config.test_helpers import AuthTestHelper
from books.models import Book

User = get_user_model()


class RatingCRUDTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(
            title="Test Book", slug="test-book", isbn="9781234567890"
        )
        cls.put_url = "/api/ratings/"
        cls.list_url = "/api/ratings/"

    # ── PUT create (201) ──────────────────────────────────────────────

    # NOTE: All tests use force_authenticate (not force_login) — this is the
    # standard pattern for JWT-based API tests throughout the project.

    def test_put_create_rating_returns_201(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.put(
            self.put_url,
            {"book_slug": "test-book", "rating": 4},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["book_slug"], "test-book")
        self.assertEqual(resp.data["rating"], 4)
        self.assertIn("id", resp.data)

    # ── PUT update (200) ──────────────────────────────────────────────

    def test_put_update_rating_returns_200(self):
        self.client.force_authenticate(user=self.user)
        # Create first
        self.client.put(
            self.put_url,
            {"book_slug": "test-book", "rating": 3},
            format="json",
        )
        # Update
        resp = self.client.put(
            self.put_url,
            {"book_slug": "test-book", "rating": 5},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["rating"], 5)

    # ── GET list ──────────────────────────────────────────────────────

    def test_get_list_returns_only_user_ratings(self):
        self.client.force_authenticate(user=self.user)
        # Create 2 ratings
        book2 = Book.objects.create(
            title="Another", slug="another", isbn="9781234567891"
        )
        self.client.put(
            self.put_url, {"book_slug": "test-book", "rating": 3}, format="json"
        )
        self.client.put(
            self.put_url, {"book_slug": "another", "rating": 2}, format="json"
        )
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 2)

    # ── GET list (empty with book_slug filter) ────────────────────────

    def test_get_list_empty_with_book_slug_filter(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(self.list_url, {"book_slug": "test-book"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    # ── GET detail ────────────────────────────────────────────────────

    def test_get_detail_returns_rating(self):
        self.client.force_authenticate(user=self.user)
        create_resp = self.client.put(
            self.put_url, {"book_slug": "test-book", "rating": 4}, format="json"
        )
        rating_id = create_resp.data["id"]
        resp = self.client.get(f"/api/ratings/{rating_id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["book_slug"], "test-book")
        self.assertEqual(resp.data["rating"], 4)

    # ── DELETE (204) ──────────────────────────────────────────────────

    def test_delete_rating_returns_204(self):
        self.client.force_authenticate(user=self.user)
        create_resp = self.client.put(
            self.put_url, {"book_slug": "test-book", "rating": 3}, format="json"
        )
        rating_id = create_resp.data["id"]
        resp = self.client.delete(f"/api/ratings/{rating_id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    # ── DELETE 404 ────────────────────────────────────────────────────

    def test_delete_nonexistent_rating_returns_404(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete("/api/ratings/99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
```

### Verify

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test ratings.tests.test_ratings.RatingCRUDTest -v 2
# Expected: 7 tests passed
```

### Commit

```bash
git add backend-django/ratings/tests/test_ratings.py
git commit -m "test(ratings): add CRUD tests — PUT create/update, GET list/detail, DELETE"
```

---

## Task 9: Test — Uniqueness (2 tests)

- [ ] Append to `backend-django/ratings/tests/test_ratings.py`

### Append to file: `backend-django/ratings/tests/test_ratings.py`

```python
class RatingUniquenessTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(
            title="Unique Test", slug="unique-test", isbn="9781234567892"
        )
        cls.put_url = "/api/ratings/"

    def test_double_put_same_book_is_update_not_400(self):
        self.client.force_authenticate(user=self.user)
        # First PUT
        r1 = self.client.put(
            self.put_url, {"book_slug": "unique-test", "rating": 4}, format="json"
        )
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)
        # Second PUT same user+book
        r2 = self.client.put(
            self.put_url, {"book_slug": "unique-test", "rating": 2}, format="json"
        )
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        self.assertEqual(r2.data["rating"], 2)

    def test_unique_constraint_prevents_duplicate_direct_create(self):
        from ratings.models import Rating
        from django.db import IntegrityError

        Rating.objects.create(user=self.user, book=self.book, rating=5)
        with self.assertRaises(IntegrityError):
            Rating.objects.create(user=self.user, book=self.book, rating=3)
```

### Verify

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test ratings.tests.test_ratings.RatingUniquenessTest -v 2
# Expected: 2 tests passed
```

### Commit

```bash
git add backend-django/ratings/tests/test_ratings.py
git commit -m "test(ratings): add uniqueness tests — upsert duplicate, unique(user,book) constraint"
```

---

## Task 10: Test — Signal (avg_rating) (3 tests)

- [ ] Append to `backend-django/ratings/tests/test_ratings.py`

### Append to file: `backend-django/ratings/tests/test_ratings.py`

```python
from ratings.models import Rating


class AvgRatingSignalTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(
            title="Signal Test", slug="signal-test", isbn="9781234567893"
        )
        cls.user2 = User.objects.create_user(
            email="user2@test.com", handle="user2", password="password123"
        )
        cls.put_url = "/api/ratings/"

    def test_avg_rating_recalculated_after_save(self):
        self.client.force_authenticate(user=self.user)
        self.client.put(
            self.put_url, {"book_slug": "signal-test", "rating": 4}, format="json"
        )
        self.book.refresh_from_db()
        self.assertEqual(self.book.avg_rating, 4.0)
        self.assertEqual(self.book.ratings_count, 1)

        # Add second rating from user2
        Rating.objects.create(user=self.user2, book=self.book, rating=2)
        self.book.refresh_from_db()
        self.assertEqual(self.book.avg_rating, 3.0)   # (4+2)/2
        self.assertEqual(self.book.ratings_count, 2)

    def test_avg_rating_recalculated_after_delete(self):
        self.client.force_authenticate(user=self.user)
        create_resp = self.client.put(
            self.put_url, {"book_slug": "signal-test", "rating": 5}, format="json"
        )
        rating_id = create_resp.data["id"]
        # Delete
        self.client.delete(f"/api/ratings/{rating_id}/")
        self.book.refresh_from_db()
        self.assertEqual(self.book.avg_rating, 0.0)
        self.assertEqual(self.book.ratings_count, 0)

    def test_ratings_count_is_correct_after_multiple_operations(self):
        self.client.force_authenticate(user=self.user)
        self.client.put(
            self.put_url, {"book_slug": "signal-test", "rating": 3}, format="json"
        )
        Rating.objects.create(user=self.user2, book=self.book, rating=5)
        self.book.refresh_from_db()
        self.assertEqual(self.book.ratings_count, 2)

        # Delete user2's rating
        Rating.objects.filter(user=self.user2, book=self.book).delete()
        self.book.refresh_from_db()
        self.assertEqual(self.book.ratings_count, 1)
```

### Verify

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test ratings.tests.test_ratings.AvgRatingSignalTest -v 2
# Expected: 3 tests passed
```

### Commit

```bash
git add backend-django/ratings/tests/test_ratings.py
git commit -m "test(ratings): add avg_rating signal tests — recalc after save, delete, count"
```

---

## Task 11: Test — Permissions (2 tests)

- [ ] Append to `backend-django/ratings/tests/test_ratings.py`

### Append to file: `backend-django/ratings/tests/test_ratings.py`

```python
class RatingPermissionTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(
            title="Permission Book", slug="perm-book", isbn="9781234567894"
        )
        cls.user_b = User.objects.create_user(
            email="userb@test.com", handle="userb", password="password123"
        )
        cls.put_url = "/api/ratings/"

    def test_anonymous_put_returns_401(self):
        resp = self.client.put(
            self.put_url,
            {"book_slug": "perm-book", "rating": 3},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_a_cannot_see_user_b_ratings(self):
        # User B creates a rating
        self.client.force_authenticate(user=self.user_b)
        resp_b = self.client.put(
            self.put_url, {"book_slug": "perm-book", "rating": 5}, format="json"
        )
        rating_id = resp_b.data["id"]

        # User A tries to access User B's rating
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(f"/api/ratings/{rating_id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        # User A's list should be empty
        resp_list = self.client.get("/api/ratings/")
        self.assertEqual(len(resp_list.data), 0)
```

### Verify

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test ratings.tests.test_ratings.RatingPermissionTest -v 2
# Expected: 2 tests passed
```

### Commit

```bash
git add backend-django/ratings/tests/test_ratings.py
git commit -m "test(ratings): add permission tests — anonymous 401, cross-user isolation"
```

---

## Task 12: Test — Validation (2 tests)

- [ ] Append to `backend-django/ratings/tests/test_ratings.py`

### Append to file: `backend-django/ratings/tests/test_ratings.py`

```python
class RatingValidationTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(
            title="Validation Book", slug="valid-book", isbn="9781234567895"
        )
        cls.put_url = "/api/ratings/"

    def test_rating_zero_returns_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.put(
            self.put_url,
            {"book_slug": "valid-book", "rating": 0},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rating_six_returns_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.put(
            self.put_url,
            {"book_slug": "valid-book", "rating": 6},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
```

### Verify

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test ratings.tests.test_ratings.RatingValidationTest -v 2
# Expected: 2 tests passed
```

### Commit

```bash
git add backend-django/ratings/tests/test_ratings.py
git commit -m "test(ratings): add validation tests — rating 0 and 6 return 400"
```

---

## Task 13: Test — Book 404 (1 test)

- [ ] Append to `backend-django/ratings/tests/test_ratings.py`

### Append to file: `backend-django/ratings/tests/test_ratings.py`

```python
class RatingBookNotFoundTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.put_url = "/api/ratings/"

    def test_put_nonexistent_book_slug_returns_404(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.put(
            self.put_url,
            {"book_slug": "nonexistent-book", "rating": 3},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
```

### Verify

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test ratings.tests.test_ratings.RatingBookNotFoundTest -v 2
# Expected: 1 test passed
```

### Commit

```bash
git add backend-django/ratings/tests/test_ratings.py
git commit -m "test(ratings): add 404 test — PUT with nonexistent book_slug"
```

---

## Task 14: Full verify + lint + final commit

- [ ] Run the full test suite for ratings
- [ ] Run ruff lint on the backend
- [ ] Final verification

### Shell commands

```bash
# Full test run
cd backend-django && DJANGO_ENV=dev uv run python manage.py test ratings -v 2
# Expected: 17 tests passed (7 CRUD + 2 uniqueness + 3 signal + 2 permissions + 2 validation + 1 book404)
#
# Note: 17 tests is correct — the milestone spec lists 15, but we added:
#   - Book 404 test (Task 13) — beneficial extra coverage
#   - Empty list with book_slug filter test (Task 8) — beneficial extra coverage
# Both extensions are explicitly kept.

# Lint
cd backend-django && uv run ruff check .
# Expected: All checks passed!

# System check
cd backend-django && DJANGO_ENV=dev uv run python manage.py check
# Expected: System check identified no issues (0 silenced).
```

### Commit

```bash
git status
# Should show only ratings/ files are modified (no unexpected changes)

git add backend-django/
git commit -m "test(ratings): verify full test suite (17 tests passing), ruff clean"
```

---

## Summary: Files created/modified

| File | Action | Tasks |
|------|--------|-------|
| `backend-django/ratings/__init__.py` | CREATE | 1 |
| `backend-django/ratings/apps.py` | CREATE | 1 |
| `backend-django/ratings/models.py` | CREATE | 2 |
| `backend-django/ratings/serializers.py` | CREATE | 3 |
| `backend-django/ratings/views.py` | CREATE | 4 |
| `backend-django/ratings/urls.py` | CREATE | 7 |
| `backend-django/ratings/signals.py` | CREATE | 5 |
| `backend-django/ratings/tests/__init__.py` | CREATE | 1 |
| `backend-django/ratings/tests/test_ratings.py` | CREATE | 8–13 |
| `backend-django/ratings/migrations/0001_initial.py` | AUTO | 2 |
| `backend-django/config/settings/base.py` | MODIFY | 1 |
| `backend-django/config/urls.py` | MODIFY | 7 |
| `backend-django/reviews/signals.py` | DELETE | 6 |
| `backend-django/reviews/apps.py` | MODIFY | 6 |

## Total: 14 tasks, 17 tests, 10 commits
