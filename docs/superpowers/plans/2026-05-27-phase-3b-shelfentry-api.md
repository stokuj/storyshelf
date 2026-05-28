# Phase 3b: ShelfEntry CRUD API — Implementation Plan

> **Prerequisite:** Phase 3a (`ratings/` app) should be implemented first for the frontend to fetch and merge ratings client-side, but the ShelfEntry API itself has no hard dependency on the ratings model.
>
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** User-scoped CRUD API for ShelfEntry: status tracking, current_page progress, nested book data. `user_rating` via Subquery annotation from `ratings.Rating`.

**Architecture:** Modify existing `shelf/` app. Remove `personal_rating`, add `current_page` with validation. New serializer with `BookNestedSerializer`. `ModelViewSet` without pagination.

**Tech Stack:** Django 6, DRF, pytest, uv.

---

## Task 1: Modify ShelfEntry model

**File:** `backend-django/shelf/models.py`

**Workdir:** `backend-django/`

Remove `personal_rating` entirely (including the `# NOTE:` comment). Add `current_page` field. Extend `clean()` with `current_page > book.page_count` validation.

### Exact code diff

Remove lines 31-35 (the `personal_rating` field and its comment), then add `current_page` after `finish_date`. Update `clean()`:

```python
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify


class ShelfEntry(models.Model):
    class Status(models.TextChoices):
        WANT_TO_READ = "WANT_TO_READ"
        READING = "READING"
        READ = "READ"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shelf_entries",
        db_index=True,
    )
    book = models.ForeignKey(
        "books.Book",
        on_delete=models.CASCADE,
        related_name="shelf_entries",
        db_index=True,
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.WANT_TO_READ
    )
    start_date = models.DateField(null=True, blank=True)
    finish_date = models.DateField(null=True, blank=True)
    current_page = models.IntegerField(
        null=True, blank=True, validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "book"], name="unique_user_book_shelf"),
        ]
        ordering = ("-created_at",)

    def clean(self):
        if self.start_date and self.finish_date and self.finish_date < self.start_date:
            raise ValidationError({"finish_date": "finish_date cannot be before start_date."})
        if (
            self.current_page is not None
            and self.book_id is not None
            and self.book.page_count is not None
            and self.current_page > self.book.page_count
        ):
            raise ValidationError({
                "current_page": (
                    f"current_page ({self.current_page}) "
                    f"cannot exceed book.page_count ({self.book.page_count})."
                )
            })
```

Note: accessing `self.book.page_count` in `clean()` triggers a lazy query if `self.book` hasn't been prefetched. This is fine — `ModelSerializer.save()` calls `full_clean()` before saving, and DRF's `SlugRelatedField` resolves `self.book` before validation runs.

Also remove the unused import `MaxValueValidator` from the top of the file (it was only used by `personal_rating`). `MinValueValidator` stays because `current_page` uses it.

**Full updated `models.py` top:**

```python
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify
```

---

## Task 2: Migrations

**Workdir:** `backend-django/`

- [ ] Generate two migrations (remove personal_rating + add current_page):

```bash
uv run python manage.py makemigrations shelf
```

Expected output: Created `0004_remove_shelfentry_personal_rating.py` and `0005_shelfentry_current_page.py`.

- [ ] Apply migrations:

```bash
uv run python manage.py migrate
```

Expected output: `Applying shelf.0004_remove_shelfentry_personal_rating... OK`, `Applying shelf.0005_shelfentry_current_page... OK`.

- [ ] Verify model state:

```bash
uv run python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

- [ ] Commit:

```bash
git add backend-django/shelf/models.py backend-django/shelf/migrations/0004_remove_shelfentry_personal_rating.py backend-django/shelf/migrations/0005_shelfentry_current_page.py
git commit -m "feat(shelf): remove personal_rating, add current_page with validation"
```

---

## Task 3: Create serializers

**File:** `backend-django/shelf/serializers.py` (new)

**Workdir:** `backend-django/`

```python
from books.models import Book
from rest_framework import serializers

from .models import ShelfEntry


class BookNestedSerializer(serializers.Serializer):
    slug = serializers.CharField()
    title = serializers.CharField()
    cover_url = serializers.CharField()
    authors = serializers.SerializerMethodField()
    genres = serializers.SerializerMethodField()
    avg_rating = serializers.FloatField(allow_null=True)
    page_count = serializers.IntegerField(allow_null=True)

    def get_authors(self, obj):
        return [{"name": ba.author.name} for ba in obj.bookauthor_set.all()]

    def get_genres(self, obj):
        return [{"name": bg.genre.name} for bg in obj.book_genre_through.all()]


class ShelfEntrySerializer(serializers.ModelSerializer):
    book_slug = serializers.SlugRelatedField(
        slug_field="slug", queryset=Book.objects.all(), source="book"
    )
    book = BookNestedSerializer(source="book", read_only=True)
    user_rating = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = ShelfEntry
        fields = [
            "id",
            "book_slug",
            "status",
            "start_date",
            "finish_date",
            "current_page",
            "user_rating",
            "book",
        ]
        read_only_fields = ["id", "book"]
```

- [ ] Commit:

```bash
git add backend-django/shelf/serializers.py
git commit -m "feat(shelf): add serializers with BookNestedSerializer and ShelfEntrySerializer"
```

---

## Task 4: Create view

**File:** `backend-django/shelf/views.py` (new)

**Workdir:** `backend-django/`

```python
from django.db.models import OuterRef, Subquery
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from ratings.models import Rating
from .models import ShelfEntry
from .serializers import ShelfEntrySerializer


class ShelfEntryViewSet(viewsets.ModelViewSet):
    serializer_class = ShelfEntrySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        user_rating_subquery = Rating.objects.filter(
            user=OuterRef("user"), book=OuterRef("book")
        ).values("rating")[:1]
        return (
            ShelfEntry.objects.filter(user=self.request.user)
            .annotate(user_rating=Subquery(user_rating_subquery))
            .select_related("book")
            .prefetch_related(
                "book__bookauthor_set__author",
                "book__book_genre_through__genre",
            )
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
```

- [ ] Commit:

```bash
git add backend-django/shelf/views.py
git commit -m "feat(shelf): add ShelfEntryViewSet with user-scoped queryset"
```

---

## Task 5: Wire up URLs

### 5a: Create `shelf/urls.py`

**File:** `backend-django/shelf/urls.py` (new)

```python
from rest_framework.routers import DefaultRouter

from .views import ShelfEntryViewSet

router = DefaultRouter()
router.register(r"entries", ShelfEntryViewSet, basename="shelfentry")
urlpatterns = router.urls
```

### 5b: Wire into `config/urls.py`

**File:** `backend-django/config/urls.py`

Add the `shelf` include after the existing `api/` routes. Full updated file:

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
    path("api/shelf/", include("shelf.urls")),
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

- [ ] Verify URL resolution:

```bash
uv run python manage.py show_urls 2>/dev/null || uv run python manage.py check
```

- [ ] Commit:

```bash
git add backend-django/shelf/urls.py backend-django/config/urls.py
git commit -m "feat(shelf): register /api/shelf/entries/ in URL config"
```

---

## Task 6: Tests

### 6a: Create test directory

```bash
mkdir -p backend-django/shelf/tests
```

**File:** `backend-django/shelf/tests/__init__.py` (new, empty)

```python
```

### 6b: Create test file

**File:** `backend-django/shelf/tests/test_shelf_entries.py` (new)

```python
from datetime import date, timedelta

from books.models import Book
from django.contrib.auth import get_user_model
from library.models import Author, Genre
from rest_framework import status
from rest_framework.test import APITestCase
from shelf.models import ShelfEntry

User = get_user_model()


class ShelfEntryAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Users
        cls.user = User.objects.create_user(
            email="alice@test.com", handle="alice", password="password123"
        )
        cls.other_user = User.objects.create_user(
            email="bob@test.com", handle="bob", password="password123"
        )

        # Author + Genre
        cls.author = Author.objects.create(name="J.R.R. Tolkien")
        cls.genre = Genre.objects.create(name="Fantasy")

        # Books
        cls.book = Book.objects.create(
            title="The Fellowship of the Ring",
            slug="the-fellowship-of-the-ring",
            page_count=423,
        )
        cls.book.authors.add(cls.author)
        cls.book.genres.add(cls.genre)

        cls.book_no_pages = Book.objects.create(
            title="Unknown Pages Book",
            slug="unknown-pages-book",
            page_count=None,
        )
        cls.book_no_pages.authors.add(cls.author)
        cls.book_no_pages.genres.add(cls.genre)

        # Base URL
        cls.list_url = "/api/shelf/entries/"

        # Helper
        cls.today = date.today()

    def _detail_url(self, entry_id):
        return f"/api/shelf/entries/{entry_id}/"

    # ── CRUD ──────────────────────────────────────────────

    def test_create_shelfentry_returns_201(self):
        """POST creates a ShelfEntry with default status WANT_TO_READ."""
        self.client.force_authenticate(self.user)
        payload = {"book_slug": self.book.slug}
        resp = self.client.post(self.list_url, payload)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["status"], "WANT_TO_READ")
        self.assertEqual(resp.data["book_slug"], self.book.slug)
        self.assertEqual(resp.data["book"]["slug"], self.book.slug)
        self.assertEqual(resp.data["book"]["title"], self.book.title)
        self.assertIsNone(resp.data["current_page"])
        self.assertIsNone(resp.data["user_rating"])

    def test_list_returns_user_entries(self):
        """GET list returns all entries for the authenticated user."""
        self.client.force_authenticate(self.user)
        ShelfEntry.objects.create(user=self.user, book=self.book)
        ShelfEntry.objects.create(
            user=self.user,
            book=self.book_no_pages,
            status="READING",
            current_page=42,
        )
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 2)

    def test_detail_returns_entry(self):
        """GET detail returns a single ShelfEntry with nested book data."""
        self.client.force_authenticate(self.user)
        entry = ShelfEntry.objects.create(
            user=self.user,
            book=self.book,
            status="READING",
            start_date=self.today - timedelta(days=5),
            current_page=100,
        )
        resp = self.client.get(self._detail_url(entry.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["status"], "READING")
        self.assertEqual(resp.data["current_page"], 100)
        self.assertEqual(resp.data["book"]["authors"][0]["name"], "J.R.R. Tolkien")
        self.assertEqual(resp.data["book"]["genres"][0]["name"], "Fantasy")

    def test_patch_status_updates_entry(self):
        """PATCH changes the status."""
        self.client.force_authenticate(self.user)
        entry = ShelfEntry.objects.create(user=self.user, book=self.book)
        resp = self.client.patch(
            self._detail_url(entry.id),
            {"status": "READING"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["status"], "READING")

    def test_delete_returns_204(self):
        """DELETE removes the entry."""
        self.client.force_authenticate(self.user)
        entry = ShelfEntry.objects.create(user=self.user, book=self.book)
        resp = self.client.delete(self._detail_url(entry.id))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ShelfEntry.objects.filter(id=entry.id).exists())

    # ── Validation ───────────────────────────────────────

    def test_finish_before_start_returns_400(self):
        """finish_date < start_date raises ValidationError."""
        self.client.force_authenticate(self.user)
        payload = {
            "book_slug": self.book.slug,
            "start_date": str(self.today),
            "finish_date": str(self.today - timedelta(days=1)),
        }
        resp = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_current_page_exceeds_page_count_returns_400(self):
        """current_page > book.page_count raises ValidationError."""
        self.client.force_authenticate(self.user)
        payload = {
            "book_slug": self.book.slug,
            "current_page": 999,
        }
        resp = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_current_page_ok_when_page_count_null(self):
        """current_page is accepted when book.page_count is None."""
        self.client.force_authenticate(self.user)
        payload = {
            "book_slug": self.book_no_pages.slug,
            "current_page": 500,
        }
        resp = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["current_page"], 500)

    def test_missing_book_slug_returns_400(self):
        """POST without book_slug returns 400."""
        self.client.force_authenticate(self.user)
        resp = self.client.post(self.list_url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Duplicate ────────────────────────────────────────

    def test_duplicate_user_book_returns_400(self):
        """POST with existing user+book pair returns 400 (UniqueConstraint)."""
        self.client.force_authenticate(self.user)
        ShelfEntry.objects.create(user=self.user, book=self.book)
        resp = self.client.post(
            self.list_url,
            {"book_slug": self.book.slug},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Isolation ────────────────────────────────────────

    def test_user_a_cannot_see_user_b_entries(self):
        """User A's list does not include User B's entries."""
        ShelfEntry.objects.create(user=self.other_user, book=self.book)
        self.client.force_authenticate(self.user)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 0)

    def test_patch_another_users_entry_returns_404(self):
        """PATCH on another user's entry returns 404 (not in queryset)."""
        entry = ShelfEntry.objects.create(user=self.other_user, book=self.book)
        self.client.force_authenticate(self.user)
        resp = self.client.patch(
            self._detail_url(entry.id),
            {"status": "READ"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    # ── Transitions ──────────────────────────────────────

    def test_read_to_want_to_read_transition(self):
        """Changing status from READ to WANT_TO_READ works (no transition restrictions)."""
        self.client.force_authenticate(self.user)
        entry = ShelfEntry.objects.create(
            user=self.user,
            book=self.book,
            status="READ",
        )
        resp = self.client.patch(
            self._detail_url(entry.id),
            {"status": "WANT_TO_READ"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["status"], "WANT_TO_READ")

    # ── user_rating Subquery ──────────────────────────────

    def test_user_rating_populated_from_rating_model(self):
        """Subquery annotation populates user_rating when Rating exists."""
        from ratings.models import Rating
        Rating.objects.create(user=self.user, book=self.book, rating=4)
        self.client.force_authenticate(self.user)
        entry = ShelfEntry.objects.create(user=self.user, book=self.book)
        resp = self.client.get(self._detail_url(entry.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["user_rating"], 4)

    def test_user_rating_null_when_no_rating(self):
        """Subquery annotation returns None when no Rating exists."""
        self.client.force_authenticate(self.user)
        entry = ShelfEntry.objects.create(user=self.user, book=self.book)
        resp = self.client.get(self._detail_url(entry.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsNone(resp.data["user_rating"])
```

### 6c: Run tests

```bash
DJANGO_ENV=dev uv run python manage.py test shelf.tests.test_shelf_entries -v2
```

Expected: 15 tests pass.

- [ ] Commit:

```bash
git add backend-django/shelf/tests/
git commit -m "test(shelf): 15 tests for ShelfEntry CRUD, validation, isolation, transitions, user_rating Subquery"
```

---

## Task 7: Final verification

**Workdir:** `backend-django/`

- [ ] Full test run:

```bash
DJANGO_ENV=dev uv run python manage.py test shelf
```

- [ ] Ruff lint:

```bash
uv run ruff check shelf/
```

Expected: `All checks passed!`

- [ ] Django system check:

```bash
uv run python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

---

## Dependency note

Phase 3b imports from `ratings.models.Rating` for the Subquery annotation in `get_queryset()`. **Phase 3a must be complete before 3b** — the `Rating` model and `ratings` app must be installed.

The `user_rating` field is populated via `Subquery(OuterRef("user"), OuterRef("book"))` — a single DB query, no N+1. When no Rating exists for the (user, book) pair, the annotation returns `None`.

---

## File manifest

| File | Action | Task |
|------|--------|------|
| `backend-django/shelf/models.py` | Modify | Task 1 |
| `backend-django/shelf/migrations/0004_*.py` | Generate | Task 2 |
| `backend-django/shelf/migrations/0005_*.py` | Generate | Task 2 |
| `backend-django/shelf/serializers.py` | Create | Task 3 |
| `backend-django/shelf/views.py` | Create | Task 4 |
| `backend-django/shelf/urls.py` | Create | Task 5 |
| `backend-django/config/urls.py` | Modify | Task 5 |
| `backend-django/shelf/tests/__init__.py` | Create | Task 6 |
| `backend-django/shelf/tests/test_shelf_entries.py` | Create | Task 6 |

## API surface summary

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| `GET` | `/api/shelf/entries/` | required | List all user's entries (no pagination) |
| `POST` | `/api/shelf/entries/` | required | Add book to shelf (default: WANT_TO_READ) |
| `GET` | `/api/shelf/entries/{id}/` | required | Entry detail with nested book |
| `PATCH` | `/api/shelf/entries/{id}/` | required | Update status/dates/current_page |
| `DELETE` | `/api/shelf/entries/{id}/` | required | Remove entry |
| `PUT` | — | — | Not supported (only PATCH) |
