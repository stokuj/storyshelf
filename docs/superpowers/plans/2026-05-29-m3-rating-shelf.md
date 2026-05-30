# M3 — Reading Statuses + Ratings — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build M3 — ratings (`ratings/` app + signal + API) and reading-status shelf (`shelf/` app + API + `/shelf` page + book-detail controls), so a user can rate books 1–5 and track Want-to-Read / Reading / Read with page progress.

**Architecture:** One plan, four task groups. **Group 0 (Foundation, sequential)** creates both apps, both models, both migrations, and all *shared-file* wiring (`INSTALLED_APPS`, `config/urls.py`, url stubs) — establishing the `ratings.Rating` import contract. Then **lanes A (ratings backend), B (shelf backend), C (frontend) run in parallel** on disjoint file sets. **Group D (Integration + E2E, sequential)** regenerates the OpenAPI snapshot/types, runs the full suites, and adds Playwright E2E.

**Tech Stack:** Django 6, DRF, `DJANGO_ENV=dev uv run python manage.py test`, ruff (backend); SvelteKit 2 + Svelte 5 runes, Tailwind v4, TypeScript, svelte-sonner, Playwright (frontend).

**Spec:** `docs/superpowers/specs/2026-05-29-m3-rating-shelf-design.md`

---

## How to execute (parallelism)

```
Group 0 (Foundation)          ← sequential, one agent, MUST finish first
   │
   ├── Lane A (ratings BE)     ┐
   ├── Lane B (shelf BE)       ├ run in parallel — disjoint files, no shared edits
   └── Lane C (frontend)       ┘
   │
Group D (Integration + E2E)   ← sequential, one agent, after A+B+C all green
```

**File-ownership rule (keeps lanes conflict-free):**
- Lane A edits **only** `backend-django/ratings/**` (except `models.py`, minimal `apps.py`, `urls.py` stub created in Group 0 — A overwrites its own `apps.py`/`urls.py`).
- Lane B edits **only** `backend-django/shelf/**` (same caveat).
- Lane C edits **only** `svelte-frontend/**`.
- `config/settings/base.py`, `config/urls.py`, `docs/api/openapi.yml`, generated TS types: touched **only** in Group 0 (settings/urls) and Group D (openapi/types). The parallel lanes never touch them.

Lane C builds against the **hand-written** types in `src/lib/types/shelf.ts` (matching the spec contracts). Generated `types:api` is regenerated in Group D and reconciled there.

---

# GROUP 0 — Foundation (sequential)

## Task 0.1: Scaffold `ratings/` app + Rating model + migration

**Files:**
- Create: `backend-django/ratings/__init__.py` (empty)
- Create: `backend-django/ratings/apps.py`
- Create: `backend-django/ratings/models.py`
- Create: `backend-django/ratings/tests/__init__.py` (empty)
- Create: `backend-django/ratings/urls.py`
- Modify: `backend-django/config/settings/base.py`

- [ ] **Step 1: Create the empty package files**

`backend-django/ratings/__init__.py` — empty.
`backend-django/ratings/tests/__init__.py` — empty.

- [ ] **Step 2: Create minimal `apps.py`** (no `ready()` yet — the signal is wired in Lane A)

`backend-django/ratings/apps.py`:
```python
from django.apps import AppConfig


class RatingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ratings"
```

- [ ] **Step 3: Create `models.py`**

`backend-django/ratings/models.py`:
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
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "book"], name="unique_user_book_rating"),
        ]
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.handle} → {self.book.title} ({self.rating}/5)"
```

- [ ] **Step 4: Create a urls stub** (so `config/urls.py` can include it before Lane A fills it)

`backend-django/ratings/urls.py`:
```python
urlpatterns = []
```

- [ ] **Step 5: Register the app in `INSTALLED_APPS`**

In `backend-django/config/settings/base.py`, append after `"library.apps.LibraryConfig",`:
```python
    "ratings.apps.RatingsConfig",
```

- [ ] **Step 6: Make + apply the migration**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py makemigrations ratings
# Expected: Migrations for 'ratings': ratings/migrations/0001_initial.py
cd backend-django && DJANGO_ENV=dev uv run python manage.py migrate
# Expected: Applying ratings.0001_initial... OK
cd backend-django && DJANGO_ENV=dev uv run python manage.py check
# Expected: System check identified no issues (0 silenced).
```

- [ ] **Step 7: Commit**

```bash
git add backend-django/ratings/ backend-django/config/settings/base.py
git commit -m "feat(ratings): scaffold app, Rating model, migration"
```

---

## Task 0.2: Scaffold `shelf/` app + ShelfEntry model + migration

**Files:**
- Create: `backend-django/shelf/__init__.py` (empty)
- Create: `backend-django/shelf/apps.py`
- Create: `backend-django/shelf/models.py`
- Create: `backend-django/shelf/tests/__init__.py` (empty)
- Create: `backend-django/shelf/urls.py`
- Modify: `backend-django/config/settings/base.py`

- [ ] **Step 1: Create empty package files** (`__init__.py`, `tests/__init__.py`).

- [ ] **Step 2: Create `apps.py`**

`backend-django/shelf/apps.py`:
```python
from django.apps import AppConfig


class ShelfConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shelf"
```

- [ ] **Step 3: Create `models.py`**

`backend-django/shelf/models.py`:
```python
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class ShelfEntry(models.Model):
    class Status(models.TextChoices):
        WANT_TO_READ = "WANT_TO_READ", "Want to Read"
        READING = "READING", "Reading"
        READ = "READ", "Read"

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
            raise ValidationError(
                {"finish_date": "finish_date cannot be before start_date."}
            )
        if (
            self.current_page is not None
            and self.book_id is not None
            and self.book.page_count is not None
            and self.current_page > self.book.page_count
        ):
            raise ValidationError(
                {
                    "current_page": (
                        f"current_page ({self.current_page}) cannot exceed "
                        f"book.page_count ({self.book.page_count})."
                    )
                }
            )

    def __str__(self):
        return f"{self.user.handle} · {self.book.title} [{self.status}]"
```

- [ ] **Step 4: Create urls stub**

`backend-django/shelf/urls.py`:
```python
urlpatterns = []
```

- [ ] **Step 5: Register in `INSTALLED_APPS`** — after the line just added for ratings:
```python
    "shelf.apps.ShelfConfig",
```

- [ ] **Step 6: Make + apply migration**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py makemigrations shelf
# Expected: Migrations for 'shelf': shelf/migrations/0001_initial.py
cd backend-django && DJANGO_ENV=dev uv run python manage.py migrate
# Expected: Applying shelf.0001_initial... OK
cd backend-django && DJANGO_ENV=dev uv run python manage.py check
# Expected: System check identified no issues (0 silenced).
```

- [ ] **Step 7: Commit**

```bash
git add backend-django/shelf/ backend-django/config/settings/base.py
git commit -m "feat(shelf): scaffold app, ShelfEntry model, migration"
```

---

## Task 0.3: Wire both apps into `config/urls.py`

**Files:**
- Modify: `backend-django/config/urls.py`

- [ ] **Step 1: Add both includes.** After the `path("api/", include("books.urls")),` line add:
```python
    path("api/", include("ratings.urls")),
    path("api/shelf/", include("shelf.urls")),
```

Resulting `urlpatterns` (top portion):
```python
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("library.urls")),
    path("api/auth/", include("users.urls.auth")),
    path("api/users/", include("users.urls.users")),
    path("api/u/", include("users.urls.public")),
    path("api/", include("books.urls")),
    path("api/", include("ratings.urls")),
    path("api/shelf/", include("shelf.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
```

- [ ] **Step 2: Verify**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py check
# Expected: System check identified no issues (0 silenced).
```

- [ ] **Step 3: Commit**

```bash
git add backend-django/config/urls.py
git commit -m "feat(m3): wire ratings + shelf url includes (empty stubs)"
```

> **Foundation done.** `ratings.Rating` and `shelf.ShelfEntry` exist and migrate. Lanes A, B, C may now start in parallel.

---

# LANE A — Ratings backend (parallel) · owns `backend-django/ratings/**`

## Task A1: RatingSerializer

**Files:**
- Create: `backend-django/ratings/serializers.py`

- [ ] **Step 1: Create the serializer**

`backend-django/ratings/serializers.py`:
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

- [ ] **Step 2: Verify import**

```bash
cd backend-django && DJANGO_ENV=dev uv run python -c "import django,os;os.environ.setdefault('DJANGO_ENV','dev');django.setup();from ratings.serializers import RatingSerializer;print('ok')"
# Expected: ok
```

- [ ] **Step 3: Commit**

```bash
git add backend-django/ratings/serializers.py
git commit -m "feat(ratings): add RatingSerializer (book_slug SlugRelatedField)"
```

---

## Task A2: Signal updating `Book.avg_rating` + `ratings_count` (TDD)

**Files:**
- Create: `backend-django/ratings/signals.py`
- Modify: `backend-django/ratings/apps.py` (add `ready()`)
- Create: `backend-django/ratings/tests/test_signals.py`

- [ ] **Step 1: Write the failing test**

`backend-django/ratings/tests/test_signals.py`:
```python
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from books.models import Book
from ratings.models import Rating

User = get_user_model()


class AvgRatingSignalTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="a@test.com", handle="alice", password="password123"
        )
        cls.user2 = User.objects.create_user(
            email="b@test.com", handle="bob", password="password123"
        )
        cls.book = Book.objects.create(title="Signal Test", slug="signal-test")

    def test_avg_and_count_after_save(self):
        Rating.objects.create(user=self.user, book=self.book, rating=4)
        self.book.refresh_from_db()
        self.assertEqual(self.book.avg_rating, 4.0)
        self.assertEqual(self.book.ratings_count, 1)

        Rating.objects.create(user=self.user2, book=self.book, rating=2)
        self.book.refresh_from_db()
        self.assertEqual(self.book.avg_rating, 3.0)  # (4+2)/2
        self.assertEqual(self.book.ratings_count, 2)

    def test_avg_resets_to_zero_after_all_deleted(self):
        r = Rating.objects.create(user=self.user, book=self.book, rating=5)
        r.delete()
        self.book.refresh_from_db()
        self.assertEqual(self.book.avg_rating, 0.0)
        self.assertEqual(self.book.ratings_count, 0)
```

- [ ] **Step 2: Run — expect FAIL** (avg stays 0.0 because no signal yet)

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test ratings.tests.test_signals -v2
# Expected: FAIL on test_avg_and_count_after_save (avg_rating 0.0 != 4.0)
```

- [ ] **Step 3: Implement the signal**

`backend-django/ratings/signals.py`:
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
        agg = Rating.objects.filter(book_id=book.id).aggregate(
            avg=Avg("rating"), count=Count("id")
        )
        book.avg_rating = round(agg["avg"], 2) if agg["count"] else 0.0
        book.ratings_count = agg["count"]
        book.save(update_fields=["avg_rating", "ratings_count"])
```

- [ ] **Step 4: Wire `ready()` in `apps.py`** — replace the file with:
```python
from django.apps import AppConfig


class RatingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ratings"

    def ready(self):
        import ratings.signals  # noqa: F401
```

- [ ] **Step 5: Run — expect PASS**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test ratings.tests.test_signals -v2
# Expected: 2 tests OK
```

- [ ] **Step 6: Commit**

```bash
git add backend-django/ratings/signals.py backend-django/ratings/apps.py backend-django/ratings/tests/test_signals.py
git commit -m "feat(ratings): signal recomputes Book.avg_rating + ratings_count"
```

---

## Task A3: RatingViewSet + URLs + API tests (TDD)

**Files:**
- Create: `backend-django/ratings/views.py`
- Modify: `backend-django/ratings/urls.py`
- Create: `backend-django/ratings/tests/test_api.py`

- [ ] **Step 1: Write the failing API tests**

`backend-django/ratings/tests/test_api.py`:
```python
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book
from ratings.models import Rating

User = get_user_model()

URL = "/api/ratings/"


class RatingAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="a@test.com", handle="alice", password="password123"
        )
        cls.user_b = User.objects.create_user(
            email="b@test.com", handle="bob", password="password123"
        )
        cls.book = Book.objects.create(title="Book One", slug="book-one")
        cls.book2 = Book.objects.create(title="Book Two", slug="book-two")

    # ── upsert ──
    def test_put_create_returns_201(self):
        self.client.force_authenticate(self.user)
        resp = self.client.put(URL, {"book_slug": "book-one", "rating": 4}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["book_slug"], "book-one")
        self.assertEqual(resp.data["rating"], 4)

    def test_put_update_returns_200(self):
        self.client.force_authenticate(self.user)
        self.client.put(URL, {"book_slug": "book-one", "rating": 3}, format="json")
        resp = self.client.put(URL, {"book_slug": "book-one", "rating": 5}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["rating"], 5)
        self.assertEqual(Rating.objects.filter(user=self.user, book=self.book).count(), 1)

    # ── list (user-scoped, not paginated) ──
    def test_list_returns_plain_list_of_own_ratings(self):
        self.client.force_authenticate(self.user)
        self.client.put(URL, {"book_slug": "book-one", "rating": 3}, format="json")
        self.client.put(URL, {"book_slug": "book-two", "rating": 2}, format="json")
        resp = self.client.get(URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsInstance(resp.data, list)  # pagination_class = None
        self.assertEqual(len(resp.data), 2)

    def test_list_filter_by_book_slug(self):
        self.client.force_authenticate(self.user)
        self.client.put(URL, {"book_slug": "book-one", "rating": 3}, format="json")
        resp = self.client.get(URL, {"book_slug": "book-one"})
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["book_slug"], "book-one")

    # ── delete ──
    def test_delete_returns_204(self):
        self.client.force_authenticate(self.user)
        created = self.client.put(URL, {"book_slug": "book-one", "rating": 3}, format="json")
        resp = self.client.delete(f"{URL}{created.data['id']}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    # ── validation ──
    def test_rating_out_of_range_returns_400(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(
            self.client.put(URL, {"book_slug": "book-one", "rating": 0}, format="json").status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            self.client.put(URL, {"book_slug": "book-one", "rating": 6}, format="json").status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_put_unknown_book_returns_404(self):
        self.client.force_authenticate(self.user)
        resp = self.client.put(URL, {"book_slug": "nope", "rating": 3}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    # ── permissions / isolation ──
    def test_anonymous_put_returns_401(self):
        resp = self.client.put(URL, {"book_slug": "book-one", "rating": 3}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_a_cannot_see_user_b_ratings(self):
        self.client.force_authenticate(self.user_b)
        self.client.put(URL, {"book_slug": "book-one", "rating": 5}, format="json")
        self.client.force_authenticate(self.user)
        resp = self.client.get(URL)
        self.assertEqual(len(resp.data), 0)
```

- [ ] **Step 2: Run — expect FAIL** (404, no view/url)

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test ratings.tests.test_api -v2
# Expected: FAIL (routes not registered)
```

- [ ] **Step 3: Implement the viewset**

`backend-django/ratings/views.py`:
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
    pagination_class = None  # GET returns a plain list (own ratings)
    http_method_names = ["get", "put", "delete", "head", "options"]

    def get_queryset(self):
        qs = Rating.objects.filter(user=self.request.user).select_related("book")
        book_slug = self.request.query_params.get("book_slug")
        if book_slug:
            qs = qs.filter(book__slug=book_slug)
        return qs

    def update(self, request, *args, **kwargs):
        """PUT = upsert on (user, book). 201 if created, 200 if updated."""
        book_slug = request.data.get("book_slug")
        try:
            book = Book.objects.get(slug=book_slug)
        except Book.DoesNotExist:
            return Response({"book_slug": "Book not found."}, status=status.HTTP_404_NOT_FOUND)

        # Validate the rating value via the serializer (honours 1..5 validators).
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rating, created = Rating.objects.update_or_create(
            user=request.user,
            book=book,
            defaults={"rating": serializer.validated_data["rating"]},
        )
        out = self.get_serializer(rating)
        return Response(
            out.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
```

> We override `update` (not `create`) so the upsert handler ignores `{id}` and resolves the book from `book_slug`. **`DefaultRouter` binds PUT only to the detail route (`/ratings/{pk}/`)**, so we map the routes explicitly to put `PUT` on the collection (`/api/ratings/`), per decision #18.

- [ ] **Step 4: Register the routes explicitly** — replace `backend-django/ratings/urls.py`:
```python
from django.urls import path

from .views import RatingViewSet

urlpatterns = [
    path(
        "ratings/",
        RatingViewSet.as_view({"get": "list", "put": "update"}),
        name="rating-list",
    ),
    path(
        "ratings/<int:pk>/",
        RatingViewSet.as_view({"get": "retrieve", "delete": "destroy"}),
        name="rating-detail",
    ),
]
```

- [ ] **Step 5: Run — expect PASS**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test ratings.tests.test_api -v2
# Expected: 9 tests OK
```

- [ ] **Step 6: Commit**

```bash
git add backend-django/ratings/views.py backend-django/ratings/urls.py backend-django/ratings/tests/test_api.py
git commit -m "feat(ratings): RatingViewSet PUT-upsert, user-scoped GET, DELETE + tests"
```

---

## Task A4: Lane A verify

- [ ] **Step 1: Full ratings suite + lint**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test ratings -v2
# Expected: 11 tests OK (2 signal + 9 api)
cd backend-django && uv run ruff check ratings/
# Expected: All checks passed!
```

- [ ] **Step 2: Commit (if ruff applied fixes)**

```bash
git add backend-django/ratings/
git commit -m "chore(ratings): lane verify — tests green, ruff clean" || echo "nothing to commit"
```

---

# LANE B — Shelf backend (parallel) · owns `backend-django/shelf/**`

## Task B1: Serializers (nested book as `string[]`, model-clean validation)

**Files:**
- Create: `backend-django/shelf/serializers.py`

- [ ] **Step 1: Create serializers**

`backend-django/shelf/serializers.py`:
```python
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from books.models import Book

from .models import ShelfEntry


class ShelfBookSerializer(serializers.ModelSerializer):
    # StringRelatedField → list[str], matching the M2 Book serializer and the
    # frontend `Book` type (authors: string[], genres: string[]).
    authors = serializers.StringRelatedField(many=True)
    genres = serializers.StringRelatedField(many=True)

    class Meta:
        model = Book
        fields = ["slug", "title", "cover_url", "authors", "genres", "avg_rating", "page_count"]


class ShelfEntrySerializer(serializers.ModelSerializer):
    book_slug = serializers.SlugRelatedField(
        slug_field="slug", queryset=Book.objects.all(), source="book", write_only=True
    )
    book = ShelfBookSerializer(read_only=True)
    user_rating = serializers.SerializerMethodField()

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
        read_only_fields = ["id", "book", "user_rating"]

    def get_user_rating(self, obj):
        # Populated by the view's Subquery annotation on list/retrieve;
        # absent on a freshly created instance → None.
        return getattr(obj, "user_rating", None)

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user
        book = attrs.get("book", getattr(self.instance, "book", None))

        # Uniqueness (user is not a serializer field, so DRF can't auto-check it).
        if self.instance is None and ShelfEntry.objects.filter(user=user, book=book).exists():
            raise serializers.ValidationError(
                {"book_slug": "This book is already on your shelf."}
            )

        # Reuse model.clean() for current_page / date validation (DRY).
        entry = self.instance or ShelfEntry()
        entry.user = user
        for field in ("book", "status", "start_date", "finish_date", "current_page"):
            if field in attrs:
                setattr(entry, field, attrs[field])
        try:
            entry.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)
        return attrs
```

> `book_slug` is `write_only` (input); the read side returns nested `book`. This avoids the field-name clash and matches the spec entry shape.

- [ ] **Step 2: Commit**

```bash
git add backend-django/shelf/serializers.py
git commit -m "feat(shelf): serializers — nested book (string[]), validate() via model.clean()"
```

---

## Task B2: ShelfEntryViewSet + URLs

**Files:**
- Create: `backend-django/shelf/views.py`
- Modify: `backend-django/shelf/urls.py`

- [ ] **Step 1: Create the viewset**

`backend-django/shelf/views.py`:
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
        user_rating = Rating.objects.filter(
            user=OuterRef("user"), book=OuterRef("book")
        ).values("rating")[:1]
        qs = (
            ShelfEntry.objects.filter(user=self.request.user)
            .annotate(user_rating=Subquery(user_rating))
            .select_related("book")
            .prefetch_related("book__authors", "book__genres")
            .order_by("-created_at")
        )
        book_slug = self.request.query_params.get("book_slug")
        if book_slug:
            qs = qs.filter(book__slug=book_slug)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
```

- [ ] **Step 2: Register the route** — replace `backend-django/shelf/urls.py`:
```python
from rest_framework.routers import DefaultRouter

from .views import ShelfEntryViewSet

router = DefaultRouter()
router.register(r"entries", ShelfEntryViewSet, basename="shelfentry")
urlpatterns = router.urls
```

- [ ] **Step 3: Verify**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py check
# Expected: System check identified no issues (0 silenced).
```

- [ ] **Step 4: Commit**

```bash
git add backend-django/shelf/views.py backend-django/shelf/urls.py
git commit -m "feat(shelf): ShelfEntryViewSet (Subquery user_rating, book_slug filter)"
```

---

## Task B3: Shelf API tests (TDD-style, then run)

**Files:**
- Create: `backend-django/shelf/tests/test_api.py`

- [ ] **Step 1: Write the tests**

`backend-django/shelf/tests/test_api.py`:
```python
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book
from library.models import Author, Genre
from ratings.models import Rating
from shelf.models import ShelfEntry

User = get_user_model()

URL = "/api/shelf/entries/"


class ShelfEntryAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="a@test.com", handle="alice", password="password123"
        )
        cls.other = User.objects.create_user(
            email="b@test.com", handle="bob", password="password123"
        )
        cls.author = Author.objects.create(name="J.R.R. Tolkien")
        cls.genre = Genre.objects.create(name="Fantasy")
        cls.book = Book.objects.create(title="The Hobbit", slug="the-hobbit", page_count=310)
        cls.book.authors.add(cls.author)
        cls.book.genres.add(cls.genre)
        cls.book_no_pages = Book.objects.create(title="No Pages", slug="no-pages", page_count=None)
        cls.today = date.today()

    def _detail(self, pk):
        return f"{URL}{pk}/"

    # ── CRUD ──
    def test_create_defaults_to_want_to_read(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(URL, {"book_slug": "the-hobbit"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["status"], "WANT_TO_READ")
        self.assertEqual(resp.data["book"]["slug"], "the-hobbit")
        self.assertEqual(resp.data["book"]["authors"], ["J.R.R. Tolkien"])
        self.assertEqual(resp.data["book"]["genres"], ["Fantasy"])
        self.assertIsNone(resp.data["current_page"])
        self.assertIsNone(resp.data["user_rating"])

    def test_list_returns_plain_list(self):
        self.client.force_authenticate(self.user)
        ShelfEntry.objects.create(user=self.user, book=self.book)
        resp = self.client.get(URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsInstance(resp.data, list)
        self.assertEqual(len(resp.data), 1)

    def test_filter_by_book_slug(self):
        self.client.force_authenticate(self.user)
        ShelfEntry.objects.create(user=self.user, book=self.book)
        ShelfEntry.objects.create(user=self.user, book=self.book_no_pages)
        resp = self.client.get(URL, {"book_slug": "the-hobbit"})
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["book"]["slug"], "the-hobbit")

    def test_patch_status(self):
        self.client.force_authenticate(self.user)
        entry = ShelfEntry.objects.create(user=self.user, book=self.book)
        resp = self.client.patch(self._detail(entry.id), {"status": "READING"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["status"], "READING")

    def test_delete(self):
        self.client.force_authenticate(self.user)
        entry = ShelfEntry.objects.create(user=self.user, book=self.book)
        resp = self.client.delete(self._detail(entry.id))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ShelfEntry.objects.filter(id=entry.id).exists())

    # ── validation ──
    def test_duplicate_returns_400(self):
        self.client.force_authenticate(self.user)
        ShelfEntry.objects.create(user=self.user, book=self.book)
        resp = self.client.post(URL, {"book_slug": "the-hobbit"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_current_page_exceeds_page_count_returns_400(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(URL, {"book_slug": "the-hobbit", "current_page": 999}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_current_page_ok_when_page_count_null(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(URL, {"book_slug": "no-pages", "current_page": 500}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["current_page"], 500)

    def test_finish_before_start_returns_400(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            URL,
            {
                "book_slug": "the-hobbit",
                "start_date": str(self.today),
                "finish_date": str(self.today - timedelta(days=1)),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_book_slug_returns_400(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(URL, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # ── isolation ──
    def test_anonymous_returns_401(self):
        resp = self.client.get(URL)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_a_cannot_see_user_b_entries(self):
        ShelfEntry.objects.create(user=self.other, book=self.book)
        self.client.force_authenticate(self.user)
        resp = self.client.get(URL)
        self.assertEqual(len(resp.data), 0)

    def test_patch_other_users_entry_returns_404(self):
        entry = ShelfEntry.objects.create(user=self.other, book=self.book)
        self.client.force_authenticate(self.user)
        resp = self.client.patch(self._detail(entry.id), {"status": "READ"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    # ── user_rating Subquery ──
    def test_user_rating_populated(self):
        Rating.objects.create(user=self.user, book=self.book, rating=4)
        self.client.force_authenticate(self.user)
        entry = ShelfEntry.objects.create(user=self.user, book=self.book)
        resp = self.client.get(self._detail(entry.id))
        self.assertEqual(resp.data["user_rating"], 4)

    def test_user_rating_null_when_no_rating(self):
        self.client.force_authenticate(self.user)
        entry = ShelfEntry.objects.create(user=self.user, book=self.book)
        resp = self.client.get(self._detail(entry.id))
        self.assertIsNone(resp.data["user_rating"])
```

- [ ] **Step 2: Run — expect PASS**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test shelf.tests.test_api -v2
# Expected: 15 tests OK
```

- [ ] **Step 3: Commit**

```bash
git add backend-django/shelf/tests/test_api.py
git commit -m "test(shelf): 15 tests — CRUD, validation, isolation, user_rating Subquery"
```

---

## Task B4: Lane B verify

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test shelf -v2
# Expected: 15 tests OK
cd backend-django && uv run ruff check shelf/
# Expected: All checks passed!
git add backend-django/shelf/ && git commit -m "chore(shelf): lane verify — tests green, ruff clean" || echo "nothing to commit"
```

---

# LANE C — Frontend (parallel) · owns `svelte-frontend/**`

> All API client functions take `fetchFn` and an `isServerSide` flag (default `false`). Server `load` functions pass `true`; client-side event handlers pass nothing (browser `fetch`, base `/api`). This matches `apiFetch(fetchFn, path, options?, isServerSide)`.

## Task C1: Types + API clients

**Files:**
- Create: `svelte-frontend/src/lib/types/shelf.ts`
- Create: `svelte-frontend/src/lib/api/ratings.ts`
- Create: `svelte-frontend/src/lib/api/shelf.ts`

- [ ] **Step 1: Types**

`svelte-frontend/src/lib/types/shelf.ts`:
```typescript
export type ShelfStatus = 'WANT_TO_READ' | 'READING' | 'READ';

export interface ShelfBook {
	slug: string;
	title: string;
	cover_url: string | null;
	authors: string[];
	genres: string[];
	avg_rating: number;
	page_count: number | null;
}

export interface ShelfEntry {
	id: number;
	status: ShelfStatus;
	start_date: string | null;
	finish_date: string | null;
	current_page: number | null;
	user_rating: number | null;
	book: ShelfBook;
}

/** ShelfEntry augmented (client-side) with the rating row id, for delete/un-rate. */
export interface ShelfEntryWithRating extends ShelfEntry {
	rating_id: number | null;
}

export interface ShelfEntryUpdate {
	status?: ShelfStatus;
	start_date?: string | null;
	finish_date?: string | null;
	current_page?: number | null;
}

export interface RatingResponse {
	id: number;
	book_slug: string;
	rating: number;
}
```

- [ ] **Step 2: Ratings API client**

`svelte-frontend/src/lib/api/ratings.ts`:
```typescript
import { apiFetch } from './_client';
import type { RatingResponse } from '$lib/types/shelf';

/** All of the current user's ratings (plain list). */
export function fetchRatings(fetchFn: typeof fetch, isServerSide = false) {
	return apiFetch<RatingResponse[]>(fetchFn, '/ratings/', undefined, isServerSide);
}

/** The current user's rating for one book, or null. */
export async function fetchUserRating(fetchFn: typeof fetch, bookSlug: string, isServerSide = false) {
	const { data, error } = await apiFetch<RatingResponse[]>(
		fetchFn,
		`/ratings/?book_slug=${encodeURIComponent(bookSlug)}`,
		undefined,
		isServerSide
	);
	return { data: data && data.length > 0 ? data[0] : null, error };
}

/** Upsert (PUT). 201 create / 200 update — both return the rating row. */
export function upsertRating(fetchFn: typeof fetch, bookSlug: string, rating: number) {
	return apiFetch<RatingResponse>(fetchFn, '/ratings/', {
		method: 'PUT',
		body: JSON.stringify({ book_slug: bookSlug, rating })
	});
}

export function deleteRatingById(fetchFn: typeof fetch, id: number) {
	return apiFetch<null>(fetchFn, `/ratings/${id}/`, { method: 'DELETE' });
}
```

- [ ] **Step 3: Shelf API client**

`svelte-frontend/src/lib/api/shelf.ts`:
```typescript
import { apiFetch } from './_client';
import type { ShelfEntry, ShelfEntryUpdate, ShelfStatus } from '$lib/types/shelf';

export function fetchShelfEntries(fetchFn: typeof fetch, isServerSide = false) {
	return apiFetch<ShelfEntry[]>(fetchFn, '/shelf/entries/', undefined, isServerSide);
}

/** The current user's shelf entry for one book, or null. */
export async function fetchShelfEntry(fetchFn: typeof fetch, bookSlug: string, isServerSide = false) {
	const { data, error } = await apiFetch<ShelfEntry[]>(
		fetchFn,
		`/shelf/entries/?book_slug=${encodeURIComponent(bookSlug)}`,
		undefined,
		isServerSide
	);
	return { data: data && data.length > 0 ? data[0] : null, error };
}

export function addToShelf(fetchFn: typeof fetch, bookSlug: string, status: ShelfStatus = 'WANT_TO_READ') {
	return apiFetch<ShelfEntry>(fetchFn, '/shelf/entries/', {
		method: 'POST',
		body: JSON.stringify({ book_slug: bookSlug, status })
	});
}

export function updateShelfEntry(fetchFn: typeof fetch, id: number, data: ShelfEntryUpdate) {
	return apiFetch<ShelfEntry>(fetchFn, `/shelf/entries/${id}/`, {
		method: 'PATCH',
		body: JSON.stringify(data)
	});
}

export function deleteShelfEntry(fetchFn: typeof fetch, id: number) {
	return apiFetch<null>(fetchFn, `/shelf/entries/${id}/`, { method: 'DELETE' });
}
```

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/src/lib/types/shelf.ts svelte-frontend/src/lib/api/ratings.ts svelte-frontend/src/lib/api/shelf.ts
git commit -m "feat(m3-fe): shelf/rating types + API clients"
```

---

## Task C2: RatingStars component

**Files:**
- Create: `svelte-frontend/src/lib/components/book/RatingStars.svelte`

- [ ] **Step 1: Create the component** (`data-selected` uses the *committed* `rating`, not hover, so the clear-toggle E2E is stable)

`svelte-frontend/src/lib/components/book/RatingStars.svelte`:
```svelte
<script lang="ts">
	import { Star } from 'lucide-svelte';

	interface Props {
		rating?: number | null;
		onRate?: (rating: number) => Promise<void>;
		readonly?: boolean;
		size?: 'sm' | 'md';
	}

	let { rating = null, onRate = undefined, readonly = false, size = 'md' }: Props = $props();

	const sizeCls = $derived(size === 'sm' ? 'size-3' : 'size-4');
	let hoverValue = $state(0);
	let loading = $state(false);

	const displayValue = $derived(hoverValue > 0 ? hoverValue : (rating ?? 0));

	async function handleClick(star: number) {
		if (readonly || loading || !onRate) return;
		loading = true;
		try {
			await onRate(star);
		} finally {
			loading = false;
		}
	}
</script>

<div class="inline-flex items-center gap-0.5">
	{#each [1, 2, 3, 4, 5] as star (star)}
		<button
			type="button"
			data-testid="rating-star"
			data-rating={star}
			data-selected={star <= (rating ?? 0)}
			class="transition-transform {readonly || !onRate ? 'cursor-default' : 'cursor-pointer hover:scale-110'}"
			class:text-accent={star <= displayValue}
			class:text-rule={star > displayValue}
			disabled={readonly || loading}
			aria-label="{star} star{star > 1 ? 's' : ''}"
			onclick={() => handleClick(star)}
			onmouseenter={() => {
				if (!readonly && !loading && onRate) hoverValue = star;
			}}
			onmouseleave={() => {
				hoverValue = 0;
			}}
		>
			<Star class={sizeCls} fill={star <= displayValue ? 'currentColor' : 'none'} />
		</button>
	{/each}
</div>
```

- [ ] **Step 2: Commit**

```bash
git add svelte-frontend/src/lib/components/book/RatingStars.svelte
git commit -m "feat(m3-fe): RatingStars (interactive/readonly, data-testid)"
```

---

## Task C3: ProgressBar component

**Files:**
- Create: `svelte-frontend/src/lib/components/shelf/ProgressBar.svelte`

- [ ] **Step 1: Create** (carries `data-current`/`data-total` for E2E)

`svelte-frontend/src/lib/components/shelf/ProgressBar.svelte`:
```svelte
<script lang="ts">
	interface Props {
		current: number | null;
		total: number | null;
	}

	let { current, total }: Props = $props();

	const percent = $derived(
		current != null && total != null && total > 0 ? Math.round((current / total) * 100) : null
	);
	const label = $derived(`${current ?? '?'} / ${total ?? '?'} pages`);
</script>

{#if current != null}
	<div class="w-full space-y-1" data-testid="progress-bar" data-current={current} data-total={total}>
		<div class="w-full bg-rule rounded-full h-1.5 overflow-hidden">
			<div
				class="bg-accent h-1.5 rounded-full transition-all duration-300"
				style="width:{percent ?? 0}%"
			></div>
		</div>
		<div class="flex items-center justify-between">
			<span class="text-xs text-muted">{label}</span>
			{#if percent != null}<span class="text-xs text-muted">{percent}%</span>{/if}
		</div>
	</div>
{/if}
```

- [ ] **Step 2: Commit**

```bash
git add svelte-frontend/src/lib/components/shelf/ProgressBar.svelte
git commit -m "feat(m3-fe): ProgressBar"
```

---

## Task C4: StatusDropdown component

**Files:**
- Create: `svelte-frontend/src/lib/components/shelf/StatusDropdown.svelte`

- [ ] **Step 1: Create** (self-contained dropdown — does NOT use the broken `ui/select`; options exposed as `role="option"` for E2E)

`svelte-frontend/src/lib/components/shelf/StatusDropdown.svelte`:
```svelte
<script lang="ts">
	import { ChevronDown } from 'lucide-svelte';
	import type { ShelfStatus } from '$lib/types/shelf';

	interface Props {
		currentStatus: ShelfStatus;
		onChange: (status: ShelfStatus) => Promise<void> | void;
		disabled?: boolean;
	}

	let { currentStatus, onChange, disabled = false }: Props = $props();

	const options: { value: ShelfStatus; label: string; color: string }[] = [
		{ value: 'WANT_TO_READ', label: 'Want to Read', color: 'text-info' },
		{ value: 'READING', label: 'Reading', color: 'text-warning' },
		{ value: 'READ', label: 'Read', color: 'text-success' }
	];

	let open = $state(false);
	let loading = $state(false);
	const current = $derived(options.find((o) => o.value === currentStatus));

	async function select(value: ShelfStatus) {
		if (disabled || loading || value === currentStatus) {
			open = false;
			return;
		}
		open = false;
		loading = true;
		try {
			await onChange(value);
		} finally {
			loading = false;
		}
	}
</script>

<svelte:window onkeydown={(e) => e.key === 'Escape' && (open = false)} />

<div class="relative">
	<button
		type="button"
		data-testid="status-dropdown"
		class="flex items-center justify-between gap-1.5 w-full rounded-md border border-rule bg-surface px-2.5 py-1.5 text-xs font-medium transition-colors hover:bg-paper-2 disabled:opacity-50 {current?.color ?? ''}"
		disabled={disabled || loading}
		aria-haspopup="listbox"
		aria-expanded={open}
		onclick={() => (open = !open)}
	>
		<span>{current?.label ?? currentStatus}</span>
		<ChevronDown class="size-3 text-muted transition-transform {open ? 'rotate-180' : ''}" />
	</button>

	{#if open}
		<div
			class="absolute top-full left-0 right-0 mt-1 z-20 rounded-md border border-rule bg-surface shadow-lg py-1"
			role="listbox"
		>
			{#each options as opt (opt.value)}
				<button
					type="button"
					role="option"
					aria-selected={opt.value === currentStatus}
					class="w-full text-left px-2.5 py-1.5 text-xs font-medium hover:bg-paper-2 {opt.color} {opt.value === currentStatus ? 'font-semibold' : ''}"
					onclick={() => select(opt.value)}
				>
					{opt.label}
				</button>
			{/each}
		</div>
		<button class="fixed inset-0 z-10" aria-label="Close menu" tabindex="-1" onclick={() => (open = false)}></button>
	{/if}
</div>
```

- [ ] **Step 2: Commit**

```bash
git add svelte-frontend/src/lib/components/shelf/StatusDropdown.svelte
git commit -m "feat(m3-fe): StatusDropdown (self-contained, not ui/select)"
```

---

## Task C5: ShelfBookCard component

**Files:**
- Create: `svelte-frontend/src/lib/components/shelf/ShelfBookCard.svelte`

- [ ] **Step 1: Create** (authors are `string[]` → `.join(', ')`; card carries `data-status`/`data-book-slug`)

`svelte-frontend/src/lib/components/shelf/ShelfBookCard.svelte`:
```svelte
<script lang="ts">
	import { goto } from '$app/navigation';
	import { Trash2 } from 'lucide-svelte';
	import BookCover from '$lib/components/book/BookCover.svelte';
	import RatingStars from '$lib/components/book/RatingStars.svelte';
	import ProgressBar from './ProgressBar.svelte';
	import StatusDropdown from './StatusDropdown.svelte';
	import { Badge } from '$lib/components/ui/badge';
	import type { ShelfEntryWithRating, ShelfStatus } from '$lib/types/shelf';

	interface Props {
		entry: ShelfEntryWithRating;
		onDelete: (id: number) => void;
		onRate: (bookSlug: string, rating: number, entryId: number) => Promise<void>;
		onStatusChange: (entryId: number, status: ShelfStatus) => Promise<void>;
	}

	let { entry, onDelete, onRate, onStatusChange }: Props = $props();

	const book = $derived(entry.book);
	const authors = $derived(book.authors.join(', '));
	const statusLabels: Record<ShelfStatus, string> = {
		WANT_TO_READ: 'Want to Read',
		READING: 'Reading',
		READ: 'Read'
	};

	let confirming = $state(false);

	function navigate() {
		goto(`/books/${book.slug}`);
	}
</script>

<div
	class="flex gap-4 rounded-lg border border-rule bg-surface p-4 shadow-sm hover:shadow-md transition-shadow"
	data-testid="shelf-book-card"
	data-status={entry.status}
	data-book-slug={book.slug}
>
	<button type="button" class="flex-shrink-0 cursor-pointer" onclick={navigate} aria-label="Go to book detail">
		<BookCover coverUrl={book.cover_url} title={book.title} size="sm" />
	</button>

	<div class="flex-1 min-w-0 space-y-2">
		<div class="space-y-0.5">
			<button type="button" class="text-left hover:text-accent transition-colors" onclick={navigate}>
				<h3 class="font-sans text-sm font-semibold text-ink line-clamp-1">{book.title}</h3>
			</button>
			<p class="text-xs text-muted">{authors}</p>
			<div class="flex flex-wrap items-center gap-2 pt-0.5">
				<Badge variant="outline" class="text-[10px] px-1.5 py-0">{statusLabels[entry.status]}</Badge>
				{#if book.avg_rating > 0}
					<span class="text-[10px] text-muted">★ {book.avg_rating.toFixed(1)}</span>
				{/if}
			</div>
		</div>

		<div class="pt-1">
			<RatingStars
				rating={entry.user_rating}
				onRate={(r) => onRate(book.slug, r, entry.id)}
				size="sm"
			/>
		</div>

		{#if entry.status === 'READING'}
			<ProgressBar current={entry.current_page} total={book.page_count} />
		{/if}

		<div class="flex items-center justify-between gap-2 pt-1">
			<div class="w-36">
				<StatusDropdown currentStatus={entry.status} onChange={(s) => onStatusChange(entry.id, s)} />
			</div>
			{#if confirming}
				<div class="flex items-center gap-1">
					<button
						type="button"
						data-testid="shelf-delete-confirm"
						class="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-danger bg-danger/10 hover:bg-danger/20 transition-colors"
						onclick={() => {
							confirming = false;
							onDelete(entry.id);
						}}
					>
						<Trash2 class="size-3" /><span>Confirm remove?</span>
					</button>
					<button type="button" class="rounded-md px-2 py-1 text-xs text-muted hover:text-ink" onclick={() => (confirming = false)}>
						Cancel
					</button>
				</div>
			{:else}
				<button
					type="button"
					data-testid="shelf-delete-btn"
					class="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted hover:text-danger hover:bg-danger/5 transition-colors"
					onclick={() => (confirming = true)}
				>
					<Trash2 class="size-3" /><span>Remove</span>
				</button>
			{/if}
		</div>
	</div>
</div>
```

- [ ] **Step 2: Commit**

```bash
git add svelte-frontend/src/lib/components/shelf/ShelfBookCard.svelte
git commit -m "feat(m3-fe): ShelfBookCard (inline status/rating/progress, data-testids)"
```

---

## Task C6: `/shelf` routes (auth guard + SSR load + tabs page)

**Files:**
- Create: `svelte-frontend/src/routes/shelf/+layout.server.ts`
- Create: `svelte-frontend/src/routes/shelf/+page.server.ts`
- Create: `svelte-frontend/src/routes/shelf/+page.svelte`

- [ ] **Step 1: Auth guard** (mirrors `settings/+layout.server.ts`)

`svelte-frontend/src/routes/shelf/+layout.server.ts`:
```typescript
import { redirect } from '@sveltejs/kit';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ parent, url }) => {
	const { user } = await parent();
	if (!user) {
		throw redirect(303, `/login?next=${encodeURIComponent(url.pathname)}`);
	}
	return { user };
};
```

- [ ] **Step 2: SSR loader** (entries + own ratings → merge `rating_id`)

`svelte-frontend/src/routes/shelf/+page.server.ts`:
```typescript
import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { fetchShelfEntries } from '$lib/api/shelf';
import { fetchRatings } from '$lib/api/ratings';
import type { ShelfEntryWithRating } from '$lib/types/shelf';

export const load: PageServerLoad = async ({ fetch }) => {
	const [entriesRes, ratingsRes] = await Promise.all([
		fetchShelfEntries(fetch, true),
		fetchRatings(fetch, true)
	]);

	if (entriesRes.error) {
		throw error(entriesRes.error.status || 500, entriesRes.error.detail || 'Failed to load shelf');
	}

	const ratingIdBySlug = new Map<string, number>();
	for (const r of ratingsRes.data ?? []) ratingIdBySlug.set(r.book_slug, r.id);

	const entries: ShelfEntryWithRating[] = (entriesRes.data ?? []).map((e) => ({
		...e,
		rating_id: ratingIdBySlug.get(e.book.slug) ?? null
	}));

	return { entries };
};
```

- [ ] **Step 3: Page** (3 tabs, client-side filter, optimistic mutations, `?tab=` sync, testids)

`svelte-frontend/src/routes/shelf/+page.svelte`:
```svelte
<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { BookOpen, Library, BookMarked } from 'lucide-svelte';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import ShelfBookCard from '$lib/components/shelf/ShelfBookCard.svelte';
	import { upsertRating, deleteRatingById } from '$lib/api/ratings';
	import { updateShelfEntry, deleteShelfEntry } from '$lib/api/shelf';
	import type { ShelfEntryWithRating, ShelfStatus } from '$lib/types/shelf';

	let { data }: { data: { entries: ShelfEntryWithRating[] } } = $props();

	let entries = $state(data.entries);
	let activeTab = $state<ShelfStatus>('WANT_TO_READ');

	const tabs: { id: ShelfStatus; label: string; icon: typeof BookOpen }[] = [
		{ id: 'WANT_TO_READ', label: 'Want to Read', icon: BookOpen },
		{ id: 'READING', label: 'Reading', icon: Library },
		{ id: 'READ', label: 'Read', icon: BookMarked }
	];

	const emptyMessages: Record<ShelfStatus, { title: string; description: string; cta?: { label: string; href: string } }> = {
		WANT_TO_READ: { title: 'No books waiting', description: 'Books you want to read will appear here.', cta: { label: 'Discover books', href: '/discover' } },
		READING: { title: 'Not reading anything right now', description: 'Books you are currently reading will appear here.' },
		READ: { title: 'No finished books yet', description: 'Books you have finished will appear here.' }
	};

	const filtered = $derived(entries.filter((e) => e.status === activeTab));
	const tabCounts = $derived({
		WANT_TO_READ: entries.filter((e) => e.status === 'WANT_TO_READ').length,
		READING: entries.filter((e) => e.status === 'READING').length,
		READ: entries.filter((e) => e.status === 'READ').length
	});

	$effect(() => {
		const p = $page.url.searchParams.get('tab');
		if (p === 'reading') activeTab = 'READING';
		else if (p === 'read') activeTab = 'READ';
		else if (p === 'want-to-read') activeTab = 'WANT_TO_READ';
	});

	function setTab(id: ShelfStatus) {
		activeTab = id;
		const url = new URL($page.url);
		url.searchParams.set('tab', { WANT_TO_READ: 'want-to-read', READING: 'reading', READ: 'read' }[id]);
		goto(url, { replaceState: true, noScroll: true, keepFocus: true });
	}

	async function handleStatusChange(entryId: number, newStatus: ShelfStatus) {
		const i = entries.findIndex((e) => e.id === entryId);
		if (i === -1) return;
		const prev = entries[i].status;
		entries[i] = { ...entries[i], status: newStatus };
		const { error } = await updateShelfEntry(fetch, entryId, { status: newStatus });
		if (error) {
			entries[i] = { ...entries[i], status: prev };
			toast.error('Failed to update status');
		}
	}

	async function handleRate(bookSlug: string, rating: number, entryId: number) {
		const i = entries.findIndex((e) => e.id === entryId);
		if (i === -1) return;
		const entry = entries[i];

		// Same star → un-rate
		if (rating === entry.user_rating && entry.rating_id != null) {
			entries[i] = { ...entry, user_rating: null, rating_id: null };
			const { error } = await deleteRatingById(fetch, entry.rating_id);
			if (error) {
				entries[i] = entry;
				toast.error('Failed to remove rating');
			}
			return;
		}
		entries[i] = { ...entry, user_rating: rating };
		const { data: result, error } = await upsertRating(fetch, bookSlug, rating);
		if (error || !result) {
			entries[i] = entry;
			toast.error('Failed to save rating');
		} else {
			entries[i] = { ...entries[i], user_rating: result.rating, rating_id: result.id };
		}
	}

	async function handleDelete(entryId: number) {
		const i = entries.findIndex((e) => e.id === entryId);
		if (i === -1) return;
		const removed = entries[i];
		entries = entries.filter((e) => e.id !== entryId);
		const { error } = await deleteShelfEntry(fetch, entryId);
		if (error) {
			entries = [removed, ...entries];
			toast.error('Failed to remove book');
		}
	}
</script>

<svelte:head><title>My Shelf — Storyshelf</title></svelte:head>

<main class="max-w-[1240px] mx-auto px-6 md:px-10 py-10 space-y-6">
	<div>
		<h1 class="font-display text-3xl md:text-4xl tracking-tight font-medium text-ink">My Shelf</h1>
		<p class="text-sm text-muted mt-1">Track what you read and want to read.</p>
	</div>

	<nav class="flex border-b border-rule" role="tablist">
		{#each tabs as tab (tab.id)}
			<button
				type="button"
				role="tab"
				data-testid="shelf-tab"
				data-tab={tab.id.toLowerCase()}
				aria-selected={activeTab === tab.id}
				class="flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors {activeTab === tab.id ? 'border-accent text-accent' : 'border-transparent text-muted hover:text-ink hover:border-rule'}"
				onclick={() => setTab(tab.id)}
			>
				<tab.icon class="size-4" />
				<span>{tab.label}</span>
				<span class="ml-1 rounded-full bg-paper-2 px-1.5 py-0.5 text-[10px] font-medium text-muted leading-none">{tabCounts[tab.id]}</span>
			</button>
		{/each}
	</nav>

	{#if filtered.length > 0}
		<div class="space-y-3">
			{#each filtered as entry (entry.id)}
				<ShelfBookCard {entry} onDelete={handleDelete} onRate={handleRate} onStatusChange={handleStatusChange} />
			{/each}
		</div>
	{:else}
		{@const msg = emptyMessages[activeTab]}
		<div data-testid="shelf-empty">
			<EmptyState icon={tabs.find((t) => t.id === activeTab)?.icon ?? BookOpen} title={msg.title} description={msg.description} cta={msg.cta} />
		</div>
	{/if}
</main>
```

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/src/routes/shelf/
git commit -m "feat(m3-fe): /shelf — auth guard, SSR load, 3 tabs, optimistic mutations"
```

---

## Task C7: ShelfControl + book-detail integration

**Files:**
- Create: `svelte-frontend/src/lib/components/shelf/ShelfControl.svelte`
- Modify: `svelte-frontend/src/routes/books/[slug]/+page.server.ts`
- Modify: `svelte-frontend/src/routes/books/[slug]/+page.svelte`

- [ ] **Step 1: ShelfControl** (Add-to-shelf when no entry; status + remove when present)

`svelte-frontend/src/lib/components/shelf/ShelfControl.svelte`:
```svelte
<script lang="ts">
	import { BookPlus } from 'lucide-svelte';
	import { toast } from 'svelte-sonner';
	import { Button } from '$lib/components/ui/button';
	import StatusDropdown from './StatusDropdown.svelte';
	import { addToShelf, updateShelfEntry, deleteShelfEntry } from '$lib/api/shelf';
	import type { ShelfEntry, ShelfStatus } from '$lib/types/shelf';

	interface Props {
		bookSlug: string;
		initialEntry: ShelfEntry | null;
	}

	let { bookSlug, initialEntry }: Props = $props();
	let entry = $state<ShelfEntry | null>(initialEntry);
	let busy = $state(false);

	async function add() {
		if (busy) return;
		busy = true;
		const { data, error } = await addToShelf(fetch, bookSlug, 'WANT_TO_READ');
		if (error || !data) toast.error('Failed to add to shelf');
		else entry = data;
		busy = false;
	}

	async function changeStatus(status: ShelfStatus) {
		if (!entry) return;
		const prev = entry.status;
		entry = { ...entry, status };
		const { error } = await updateShelfEntry(fetch, entry.id, { status });
		if (error) {
			entry = { ...entry, status: prev };
			toast.error('Failed to update status');
		}
	}

	async function remove() {
		if (!entry || busy) return;
		busy = true;
		const { error } = await deleteShelfEntry(fetch, entry.id);
		if (error) toast.error('Failed to remove from shelf');
		else entry = null;
		busy = false;
	}
</script>

{#if entry}
	<div class="flex items-center gap-2" data-testid="shelf-control">
		<div class="w-40"><StatusDropdown currentStatus={entry.status} onChange={changeStatus} /></div>
		<button type="button" class="text-xs text-muted hover:text-danger transition-colors" onclick={remove} disabled={busy}>
			Remove
		</button>
	</div>
{:else}
	<Button variant="outline" size="sm" onclick={add} disabled={busy} data-testid="add-to-shelf">
		<BookPlus class="mr-2 size-4" /> Add to shelf
	</Button>
{/if}
```

- [ ] **Step 2: Extend the book-detail server loader** (parallel fetch of user rating + shelf entry when authenticated)

Replace `svelte-frontend/src/routes/books/[slug]/+page.server.ts`:
```typescript
import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { getBook } from '$lib/api/books';
import { fetchUserRating } from '$lib/api/ratings';
import { fetchShelfEntry } from '$lib/api/shelf';

export const load: PageServerLoad = async ({ fetch, params, parent }) => {
	const { user } = await parent();

	const [bookRes, ratingRes, entryRes] = await Promise.all([
		getBook(fetch, params.slug),
		user ? fetchUserRating(fetch, params.slug, true) : Promise.resolve({ data: null, error: null }),
		user ? fetchShelfEntry(fetch, params.slug, true) : Promise.resolve({ data: null, error: null })
	]);

	if (bookRes.error) {
		throw error(bookRes.error.status || 500, bookRes.error.detail);
	}

	return {
		book: bookRes.data!,
		user,
		userRating: ratingRes.data ? { id: ratingRes.data.id, rating: ratingRes.data.rating } : null,
		shelfEntry: entryRes.data ?? null
	};
};
```

- [ ] **Step 3: Add RatingStars + ShelfControl to the book detail page.** In `svelte-frontend/src/routes/books/[slug]/+page.svelte`, add to the `<script>`:
```typescript
	import { toast } from 'svelte-sonner';
	import RatingStars from '$lib/components/book/RatingStars.svelte';
	import ShelfControl from '$lib/components/shelf/ShelfControl.svelte';
	import { upsertRating, deleteRatingById } from '$lib/api/ratings';

	let userRating = $state(data.userRating?.rating ?? null);
	let ratingId = $state(data.userRating?.id ?? null);
	let savingRating = $state(false);

	async function handleRate(star: number) {
		if (savingRating) return;
		savingRating = true;
		if (star === userRating && ratingId) {
			const { error } = await deleteRatingById(fetch, ratingId);
			if (error) toast.error('Failed to remove rating');
			else {
				userRating = null;
				ratingId = null;
			}
		} else {
			const { data: result, error } = await upsertRating(fetch, data.book.slug, star);
			if (error || !result) toast.error('Failed to save rating');
			else {
				userRating = result.rating;
				ratingId = result.id;
			}
		}
		savingRating = false;
	}
```
Then in the template, near the title/cover area, add a controls block:
```svelte
<div class="flex flex-col gap-3">
	<div class="flex items-center gap-2">
		<RatingStars rating={userRating} onRate={data.user ? handleRate : undefined} readonly={!data.user} />
		{#if data.book.ratings_count > 0}
			<span class="text-sm text-muted">{data.book.avg_rating.toFixed(1)} ({data.book.ratings_count})</span>
		{/if}
	</div>
	{#if data.user}
		<ShelfControl bookSlug={data.book.slug} initialEntry={data.shelfEntry} />
	{/if}
</div>
```

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/src/lib/components/shelf/ShelfControl.svelte svelte-frontend/src/routes/books/
git commit -m "feat(m3-fe): book detail — RatingStars + ShelfControl (add to shelf)"
```

---

## Task C8: "Shelf" nav link (auth-only)

**Files:**
- Modify: `svelte-frontend/src/lib/components/shell/AppShell.svelte`

- [ ] **Step 1:** In the `<nav>` block, after the Discover button, add:
```svelte
				{#if user}
					<Button variant="ghost" size="sm" href={resolve('/shelf')}>Shelf</Button>
				{/if}
```
Resulting nav:
```svelte
			<nav class="hidden md:flex items-center gap-1">
				<Button variant="ghost" size="sm" href={resolve('/discover')}>Discover</Button>
				{#if user}
					<Button variant="ghost" size="sm" href={resolve('/shelf')}>Shelf</Button>
				{/if}
			</nav>
```

- [ ] **Step 2: Commit**

```bash
git add svelte-frontend/src/lib/components/shell/AppShell.svelte
git commit -m "feat(m3-fe): add auth-only Shelf nav link"
```

---

## Task C9: Lane C verify

```bash
cd svelte-frontend && npm run check
# Expected: 0 errors
cd svelte-frontend && npm run lint
# Expected: 0 errors (run `npx prettier --write` on touched files if formatting fails, then re-commit)
git add svelte-frontend/ && git commit -m "chore(m3-fe): lane verify — check + lint clean" || echo "nothing to commit"
```

> If `npm run check` complains about `resolve('/shelf')` (route not yet in the generated route table), it resolves after the route files from Task C6 exist — they do within this lane. If a path-alias error persists, use the string `'/shelf'` directly.

---

# GROUP D — Integration + E2E (sequential, after A+B+C)

## Task D1: Regenerate OpenAPI snapshot + TS types

**Files:**
- Modify: `docs/api/openapi.yml`
- Modify: `svelte-frontend/src/lib/types/api.generated.ts`

- [ ] **Step 1: Regenerate the OpenAPI schema** (the snapshot test `config/tests/test_openapi_schema.py` compares against this file)

```bash
make regenerate-openapi
# or, if the target differs:
# cd backend-django && DJANGO_ENV=dev uv run python manage.py spectacular --file ../docs/api/openapi.yml
```

- [ ] **Step 2: Regenerate frontend types from the new schema**

```bash
cd svelte-frontend && npm run types:api
```

- [ ] **Step 3: Reconcile** — if generated types differ from the hand-written `lib/types/shelf.ts`, the hand-written types are the source of truth for the app; keep them. The generated file is only consumed where already imported. Run `npm run check` to confirm no breakage.

- [ ] **Step 4: Commit**

```bash
git add docs/api/openapi.yml svelte-frontend/src/lib/types/api.generated.ts
git commit -m "chore(m3): regenerate OpenAPI schema + API types for ratings/shelf"
```

---

## Task D2: Full backend + frontend verification

- [ ] **Step 1: Full backend suite + lint + schema snapshot test**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test
# Expected: all tests pass (194 pre-existing + 11 ratings + 15 shelf + schema test green)
cd backend-django && uv run ruff check .
# Expected: All checks passed!
```

> If `config/tests/test_openapi_schema.py` fails, re-run Task D1 Step 1 (the snapshot is stale).

- [ ] **Step 2: Frontend check + lint + build**

```bash
cd svelte-frontend && npm run check && npm run lint && npm run build
# Expected: 0 errors; production build succeeds
```

- [ ] **Step 3: Commit any fixes**

```bash
git add -A && git commit -m "chore(m3): full backend + frontend verification green" || echo "nothing to commit"
```

---

## Task D3: E2E — seed helper + shelf spec

**Files:**
- Create: `svelte-frontend/e2e/helpers/seed.ts`
- Create: `svelte-frontend/e2e/shelf-status.spec.ts`

**data-testid contract** (already baked into Lane C components):

| Element | testid | extra attrs |
|---|---|---|
| Card wrapper | `shelf-book-card` | `data-status`, `data-book-slug` |
| Tab button | `shelf-tab` | `data-tab` = `want_to_read`/`reading`/`read` |
| Empty state | `shelf-empty` | — |
| ProgressBar | `progress-bar` | `data-current`, `data-total` |
| Rating star | `rating-star` | `data-rating` (1-5), `data-selected` |
| Status trigger | `status-dropdown` | options are `role="option"` |
| Delete / confirm | `shelf-delete-btn` / `shelf-delete-confirm` | — |
| Add to shelf | `add-to-shelf` | (book detail) |

- [ ] **Step 1: Confirm test books are seeded.** E2E needs `the-hobbit` (page_count 423), `the-fellowship-of-the-ring`, `the-two-towers` in the dev DB.

```bash
cd backend-django && DJANGO_ENV=dev uv run python ../infra/scripts/seed.py || uv run python manage.py seed_books
```

- [ ] **Step 2: Create the seed helper**

`svelte-frontend/e2e/helpers/seed.ts`:
```typescript
import { type Cookie } from '@playwright/test';
import { API_BASE_URL } from '../fixtures';

export interface SeedShelfEntry {
	id: number;
	book_slug: string;
	status: string;
	current_page: number | null;
}

export async function seedShelfEntry(
	entry: { book_slug: string; status: string; current_page?: number | null },
	cookies: Cookie[],
	playwright: typeof import('@playwright/test').playwright
): Promise<SeedShelfEntry> {
	const api = await playwright.request.newContext({ baseURL: API_BASE_URL, storageState: { cookies } });
	const payload: Record<string, unknown> = { book_slug: entry.book_slug, status: entry.status };
	if (entry.current_page != null) payload.current_page = entry.current_page;
	const res = await api.post('/api/shelf/entries/', { data: payload });
	if (!res.ok()) {
		const body = await res.text();
		await api.dispose();
		throw new Error(`[seed] shelf entry failed: ${res.status()} ${body} payload=${JSON.stringify(payload)}`);
	}
	const data = await res.json();
	await api.dispose();
	return { id: data.id, book_slug: data.book.slug, status: data.status, current_page: data.current_page };
}

export async function cleanupShelfEntries(
	cookies: Cookie[],
	playwright: typeof import('@playwright/test').playwright
): Promise<void> {
	const api = await playwright.request.newContext({ baseURL: API_BASE_URL, storageState: { cookies } });
	const listRes = await api.get('/api/shelf/entries/');
	if (listRes.ok()) {
		const entries: { id: number }[] = await listRes.json();
		for (const e of entries) await api.delete(`/api/shelf/entries/${e.id}/`);
	}
	await api.dispose();
}
```

> Note: `seedShelfEntry` reads `data.book.slug` from the nested book in the POST response (matches the contract).

- [ ] **Step 3: Create the spec** (8 tests: auth redirect, add-from-detail, tabs, status move, rating toggle, progress, empty states, cross-user)

`svelte-frontend/e2e/shelf-status.spec.ts`:
```typescript
import { randomUUID } from 'node:crypto';
import { type Cookie } from '@playwright/test';
import { test, expect, API_BASE_URL } from './fixtures';
import { seedShelfEntry, cleanupShelfEntries, type SeedShelfEntry } from './helpers/seed';

const BOOKS = {
	H: { slug: 'the-hobbit', title: 'The Hobbit', page_count: 423 },
	F: { slug: 'the-fellowship-of-the-ring', title: 'The Fellowship of the Ring' },
	T: { slug: 'the-two-towers', title: 'The Two Towers' }
} as const;

async function clickTab(page: import('@playwright/test').Page, tab: 'want_to_read' | 'reading' | 'read') {
	await page.locator(`[data-testid="shelf-tab"][data-tab="${tab}"]`).click();
}

test.describe('Shelf', () => {
	test('anonymous visit to /shelf redirects to /login', async ({ page }) => {
		await page.goto('/shelf');
		await expect(page).toHaveURL(/\/login/);
	});

	test('add to shelf from book detail, then it appears on /shelf', async ({ page, authUser, playwright }) => {
		await page.goto(`/books/${BOOKS.H.slug}`);
		await page.locator('[data-testid="add-to-shelf"]').click();
		await expect(page.locator('[data-testid="shelf-control"]')).toBeVisible();

		await page.goto('/shelf');
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(1);
		await expect(page.getByText(BOOKS.H.title)).toBeVisible();

		await cleanupShelfEntries(await page.context().cookies(), playwright);
	});

	test('three tabs filter by status', async ({ page, authUser, playwright }) => {
		const cookies = await page.context().cookies();
		await seedShelfEntry({ book_slug: BOOKS.H.slug, status: 'WANT_TO_READ' }, cookies, playwright);
		await seedShelfEntry({ book_slug: BOOKS.F.slug, status: 'READING', current_page: 200 }, cookies, playwright);
		await seedShelfEntry({ book_slug: BOOKS.T.slug, status: 'READ' }, cookies, playwright);
		await page.goto('/shelf');

		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(1);
		await clickTab(page, 'reading');
		await expect(page.getByText(BOOKS.F.title)).toBeVisible();
		await clickTab(page, 'read');
		await expect(page.getByText(BOOKS.T.title)).toBeVisible();

		await cleanupShelfEntries(cookies, playwright);
	});

	test('status dropdown moves card between tabs', async ({ page, authUser, playwright }) => {
		const cookies = await page.context().cookies();
		await seedShelfEntry({ book_slug: BOOKS.H.slug, status: 'WANT_TO_READ' }, cookies, playwright);
		await page.goto('/shelf');

		await page.locator('[data-testid="status-dropdown"]').first().click();
		await page.getByRole('option', { name: 'Reading' }).click();
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(0);
		await clickTab(page, 'reading');
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(1);

		await cleanupShelfEntries(cookies, playwright);
	});

	test('rating stars set, change, and clear', async ({ page, authUser, playwright }) => {
		const cookies = await page.context().cookies();
		await seedShelfEntry({ book_slug: BOOKS.H.slug, status: 'WANT_TO_READ' }, cookies, playwright);
		await page.goto('/shelf');

		await expect(page.locator('[data-testid="rating-star"][data-selected="true"]')).toHaveCount(0);
		await page.locator('[data-testid="rating-star"][data-rating="3"]').click();
		await expect(page.locator('[data-testid="rating-star"][data-selected="true"]')).toHaveCount(3);
		await page.locator('[data-testid="rating-star"][data-rating="5"]').click();
		await expect(page.locator('[data-testid="rating-star"][data-selected="true"]')).toHaveCount(5);
		await page.locator('[data-testid="rating-star"][data-rating="5"]').click();
		await expect(page.locator('[data-testid="rating-star"][data-selected="true"]')).toHaveCount(0);

		await cleanupShelfEntries(cookies, playwright);
	});

	test('progress bar shows only in Reading tab with correct values', async ({ page, authUser, playwright }) => {
		const cookies = await page.context().cookies();
		await seedShelfEntry({ book_slug: BOOKS.H.slug, status: 'READING', current_page: 200 }, cookies, playwright);
		await page.goto('/shelf');

		await clickTab(page, 'want_to_read');
		await expect(page.locator('[data-testid="progress-bar"]')).toHaveCount(0);
		await clickTab(page, 'reading');
		const bar = page.locator('[data-testid="progress-bar"]');
		await expect(bar).toBeVisible();
		await expect(bar).toHaveAttribute('data-current', '200');
		await expect(bar).toHaveAttribute('data-total', String(BOOKS.H.page_count));

		await cleanupShelfEntries(cookies, playwright);
	});

	test('empty states per tab when shelf is empty', async ({ page, authUser }) => {
		await page.goto('/shelf');
		await expect(page.locator('[data-testid="shelf-empty"]')).toBeVisible();
		await clickTab(page, 'reading');
		await expect(page.getByText(/not reading anything/i)).toBeVisible();
		await clickTab(page, 'read');
		await expect(page.getByText(/no finished books/i)).toBeVisible();
	});

	test('user B does not see user A entries', async ({ page, authUser, playwright }) => {
		const aCookies = await page.context().cookies();
		await seedShelfEntry({ book_slug: BOOKS.H.slug, status: 'WANT_TO_READ' }, aCookies, playwright);
		await page.goto('/shelf');
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(1);

		// Register a fresh user B, swap cookies in the same browser context.
		const api = await playwright.request.newContext({ baseURL: API_BASE_URL });
		const email = `userb-${randomUUID().slice(0, 8)}@e2e.example`;
		const reg = await api.post('/api/auth/register/', { data: { email, display_name: 'User B', password: 'TestPass123!' } });
		expect(reg.ok()).toBe(true);
		const { cookies: bCookies } = await api.storageState();
		await api.dispose();

		await page.context().clearCookies();
		await page.context().addCookies(bCookies as Cookie[]);
		await page.goto('/shelf');
		await expect(page.locator('[data-testid="shelf-book-card"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="shelf-empty"]')).toBeVisible();

		// Cleanup: user B via its own cookies; user A entries via stored A cookies.
		await cleanupShelfEntries(aCookies, playwright);
		const apiB = await playwright.request.newContext({ baseURL: API_BASE_URL, storageState: { cookies: bCookies } });
		await apiB.delete('/api/users/me/', { data: { current_password: 'TestPass123!' } });
		await apiB.dispose();
	});
});
```

- [ ] **Step 3b: Run E2E** (dev stack must be up: `make dev-up`, or `npm run dev` + Django)

```bash
cd svelte-frontend && npx playwright test e2e/shelf-status.spec.ts
# Expected: 8 passed
```

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/e2e/helpers/seed.ts svelte-frontend/e2e/shelf-status.spec.ts
git commit -m "test(e2e): shelf — 8 scenarios (auth, add, tabs, status, rating, progress, empty, isolation)"
```

---

## Task D4: Final verification

- [ ] **Step 1: Everything green**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test && uv run ruff check .
cd svelte-frontend && npm run check && npm run lint
cd svelte-frontend && npx playwright test e2e/shelf-status.spec.ts
```

- [ ] **Step 2: Clean git status**

```bash
git status   # only intended M3 files changed
```

---

## Self-review checklist (run before finishing)

- [ ] `ratings.Rating` + signal: avg_rating/ratings_count correct (0.0 at zero ratings).
- [ ] `RatingViewSet` has `pagination_class = None`; PUT upsert 201/200; user-scoped GET; unknown book → 404.
- [ ] `ShelfEntry` clean() enforced via serializer `validate()` → 400 (not 500); duplicate → 400.
- [ ] Nested book authors/genres are `string[]` (StringRelatedField), matching the `Book` type.
- [ ] `user_rating` via Subquery on list/retrieve; `None` on create.
- [ ] `/shelf` auth guard; SSR load; 3 tabs; optimistic mutations; empty states.
- [ ] Book detail: RatingStars (auth-conditional) + ShelfControl (add/status/remove).
- [ ] Auth-only "Shelf" nav link in AppShell.
- [ ] All E2E `data-testid`s present on the components.
- [ ] OpenAPI snapshot + TS types regenerated; full suites + E2E green.

## File manifest

| Group | Files |
|---|---|
| 0 | `ratings/{__init__,apps,models,urls}.py`, `ratings/tests/__init__.py`, `shelf/{__init__,apps,models,urls}.py`, `shelf/tests/__init__.py`, `config/settings/base.py`, `config/urls.py`, both `migrations/0001_initial.py` |
| A | `ratings/{serializers,signals,views,urls,apps}.py`, `ratings/tests/{test_signals,test_api}.py` |
| B | `shelf/{serializers,views,urls}.py`, `shelf/tests/test_api.py` |
| C | `lib/types/shelf.ts`, `lib/api/{ratings,shelf}.ts`, `lib/components/book/RatingStars.svelte`, `lib/components/shelf/{ProgressBar,StatusDropdown,ShelfBookCard,ShelfControl}.svelte`, `routes/shelf/{+layout.server,+page.server,+page.svelte}`, `routes/books/[slug]/{+page.server.ts,+page.svelte}`, `lib/components/shell/AppShell.svelte` |
| D | `docs/api/openapi.yml`, `lib/types/api.generated.ts`, `e2e/helpers/seed.ts`, `e2e/shelf-status.spec.ts` |
