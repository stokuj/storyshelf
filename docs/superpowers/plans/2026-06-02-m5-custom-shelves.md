# M5 Custom Shelves Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pozwolić userowi tworzyć własne nazwane kolekcje książek (custom shelves), publiczne lub prywatne, niezależne od statusu czytania.

**Architecture:** Rozszerzenie app `shelf/` o modele `Shelf` + `ShelfMembership` (obok istniejącego `ShelfEntry`). Owner CRUD przez `ShelfViewSet` pod `/api/shelves/`, publiczny odczyt pod `/api/u/{handle}/shelves/` (profil bramkuje widoczność, jak `UserProfileView`). Front: zakładka „Moje półki" na `/shelf`, widok własnej półki `/shelf/[slug]`, kontrolka na `/books/[slug]`, publiczny widok `/u/[handle]/shelves/[slug]`.

**Tech Stack:** Django 6 + DRF, SvelteKit 2 + Svelte 5 + TypeScript, Playwright (E2E). Książka identyfikowana przez `book_slug` (jak `reviews/`, `shelf/`).

**Spec:** `docs/superpowers/specs/2026-06-02-m5-custom-shelves-design.md`

---

## File Structure

**Backend (`backend-django/shelf/`):**
- `models.py` — MODIFY: dodać `Shelf`, `ShelfMembership`, helper `_generate_unique_shelf_slug` (obok `ShelfEntry`).
- `serializers.py` — MODIFY: dodać `ShelfSerializer`, `ShelfDetailSerializer`, `PublicShelfSerializer`, `PublicShelfDetailSerializer` (reuse istniejącego `ShelfBookSerializer`).
- `views.py` — MODIFY: dodać `ShelfViewSet`, `PublicShelfListView`, `PublicShelfDetailView`.
- `urls_shelves.py` — CREATE: router dla `ShelfViewSet` → `/api/shelves/`.
- `urls_public.py` — CREATE: publiczne widoki → `/api/u/{handle}/shelves/`.
- `migrations/0002_shelf_shelfmembership.py` — CREATE (przez `makemigrations`).
- `tests/test_shelves.py` — CREATE: testy modeli + owner CRUD + membership + publiczne.

**Backend (inne apps):**
- `config/urls.py` — MODIFY: dodać 2 include (owner + public).
- `users/exporters.py` — MODIFY: dodać `shelves.json` do eksportu.

**Frontend (`svelte-frontend/src/`):**
- `lib/types/shelf.ts` — MODIFY: dodać typy `Shelf`, `ShelfDetail`, `PublicShelf`.
- `lib/api/shelves.ts` — CREATE: klient API custom shelves.
- `routes/shelf/+page.svelte` — MODIFY: zakładki Status / Moje półki.
- `routes/shelf/+page.server.ts` — MODIFY: doładować moje półki.
- `routes/shelf/[slug]/+page.server.ts` + `+page.svelte` — CREATE: widok własnej półki.
- `routes/books/[slug]/+page.server.ts` + `+page.svelte` — MODIFY: kontrolka „Dodaj do półki".
- `routes/u/[handle]/+page.server.ts` + `+page.svelte` — MODIFY: lista publicznych półek.
- `routes/u/[handle]/shelves/[slug]/+page.server.ts` + `+page.svelte` — CREATE: publiczny widok półki.

**E2E (`svelte-frontend/e2e/`):**
- `shelves.spec.ts` — CREATE: 4 scenariusze.

---

## Konwencje (przeczytaj przed startem)

- Backend testy: z `backend-django/`, komenda `DJANGO_ENV=dev uv run python manage.py test shelf` (lub `shelf.tests.test_shelves` dla pojedynczego pliku).
- Lint backend: `uv run ruff check .` z `backend-django/`.
- Commity: conventional, **tytuł ≤ 50 znaków**, bez `Co-Authored-By`.
- Książka zawsze przez `book_slug` (SlugRelatedField / `get_object_or_404(Book, slug=...)`).
- Slug półki: generowany z `name` przy tworzeniu, **niezmienny** po utworzeniu (stabilne publiczne URL-e). Unikat per owner.

---

## Task 1: Modele Shelf + ShelfMembership

**Files:**
- Modify: `backend-django/shelf/models.py`
- Test: `backend-django/shelf/tests/test_shelves.py` (create)

- [ ] **Step 1: Write the failing test**

Create `backend-django/shelf/tests/test_shelves.py`:

```python
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from books.models import Book
from shelf.models import Shelf, ShelfMembership

User = get_user_model()


class ShelfModelTests(TestCase):
    def setUp(self):
        self.u1 = User.objects.create_user(email="a@x.com", handle="alice", password="pw")
        self.u2 = User.objects.create_user(email="b@x.com", handle="bob", password="pw")
        self.book = Book.objects.create(title="Dune")

    def test_slug_generated_from_name(self):
        shelf = Shelf.objects.create(owner=self.u1, name="My Fantasy")
        self.assertEqual(shelf.slug, "my-fantasy")

    def test_slug_unique_per_owner_suffixes(self):
        # Same name twice would violate unique(owner, name); slug suffixing is for
        # the rare case slugify collapses two different names to the same base.
        s1 = Shelf.objects.create(owner=self.u1, name="Sci Fi")
        s2 = Shelf.objects.create(owner=self.u1, name="Sci-Fi!")
        self.assertNotEqual(s1.slug, s2.slug)

    def test_same_slug_allowed_across_owners(self):
        s1 = Shelf.objects.create(owner=self.u1, name="Fantasy")
        s2 = Shelf.objects.create(owner=self.u2, name="Fantasy")
        self.assertEqual(s1.slug, s2.slug)

    def test_duplicate_name_per_owner_rejected(self):
        Shelf.objects.create(owner=self.u1, name="Fantasy")
        with self.assertRaises(IntegrityError):
            Shelf.objects.create(owner=self.u1, name="Fantasy")

    def test_membership_unique_per_shelf_book(self):
        shelf = Shelf.objects.create(owner=self.u1, name="Fantasy")
        ShelfMembership.objects.create(shelf=shelf, book=self.book)
        with self.assertRaises(IntegrityError):
            ShelfMembership.objects.create(shelf=shelf, book=self.book)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test shelf.tests.test_shelves -v 2`
Expected: FAIL — `ImportError: cannot import name 'Shelf'`.

- [ ] **Step 3: Add models to `shelf/models.py`**

Append to `backend-django/shelf/models.py` (po `ShelfEntry`):

```python
from django.utils.text import slugify


def _generate_unique_shelf_slug(owner, name: str) -> str:
    base = slugify(name)[:80] or "shelf"
    slug = base
    counter = 1
    while Shelf.objects.filter(owner=owner, slug=slug).exists():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


class Shelf(models.Model):
    """A user-curated named collection of books (M5).

    NOTE: distinct from ShelfEntry above. ShelfEntry is reading status
    (Want to Read / Reading / Read), one per user+book. A Shelf is an
    arbitrary collection; ShelfEntry is NOT a member of a Shelf.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shelves",
        db_index=True,
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    is_public = models.BooleanField(default=False)
    slug = models.SlugField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["owner", "slug"], name="unique_owner_shelf_slug"),
            models.UniqueConstraint(fields=["owner", "name"], name="unique_owner_shelf_name"),
        ]
        ordering = ("-created_at",)

    def save(self, *args, **kwargs):
        # Slug is generated once on create and never changes (stable public URLs).
        if not self.slug:
            self.slug = _generate_unique_shelf_slug(self.owner, self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.owner.handle} · {self.name}"


class ShelfMembership(models.Model):
    shelf = models.ForeignKey(Shelf, on_delete=models.CASCADE, related_name="memberships")
    book = models.ForeignKey(
        "books.Book", on_delete=models.CASCADE, related_name="shelf_memberships"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["shelf", "book"], name="unique_shelf_book"),
        ]
        ordering = ("-added_at",)

    def __str__(self):
        return f"{self.shelf.name} · {self.book.title}"
```

- [ ] **Step 4: Create migration**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py makemigrations shelf`
Expected: creates `shelf/migrations/0002_*.py` with Shelf + ShelfMembership.

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test shelf.tests.test_shelves -v 2`
Expected: PASS (5 tests).

- [ ] **Step 6: Commit**

```bash
git add backend-django/shelf/models.py backend-django/shelf/migrations/ backend-django/shelf/tests/test_shelves.py
git commit -m "feat(shelf): add Shelf + ShelfMembership models"
```

---

## Task 2: Owner serializers

**Files:**
- Modify: `backend-django/shelf/serializers.py`

- [ ] **Step 1: Add serializers**

Append to `backend-django/shelf/serializers.py` (`ShelfBookSerializer` już istnieje na górze pliku — reuse):

```python
from .models import Shelf  # add to existing imports from .models


class ShelfSerializer(serializers.ModelSerializer):
    """List/create/update view of a shelf (no books)."""

    book_count = serializers.SerializerMethodField()
    contains_book = serializers.SerializerMethodField()

    class Meta:
        model = Shelf
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_public",
            "book_count",
            "contains_book",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "book_count", "contains_book", "created_at", "updated_at"]

    @extend_schema_field(serializers.IntegerField())
    def get_book_count(self, obj):
        # Annotated by the view; fall back to a count for un-annotated instances.
        count = getattr(obj, "book_count", None)
        return count if count is not None else obj.memberships.count()

    @extend_schema_field(serializers.BooleanField(allow_null=True))
    def get_contains_book(self, obj):
        # Only annotated when the list view is filtered by ?book_slug; else None.
        return getattr(obj, "contains_book", None)

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Shelf name cannot be empty.")
        # owner is set in the view (not a serializer field) → check uniqueness here.
        user = self.context["request"].user
        qs = Shelf.objects.filter(owner=user, name=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("You already have a shelf with this name.")
        return value


class ShelfDetailSerializer(ShelfSerializer):
    """Retrieve view: shelf + its books (newest first)."""

    books = serializers.SerializerMethodField()

    class Meta(ShelfSerializer.Meta):
        fields = ShelfSerializer.Meta.fields + ["books"]

    @extend_schema_field(ShelfBookSerializer(many=True))
    def get_books(self, obj):
        books = [
            m.book
            for m in obj.memberships.select_related("book").prefetch_related(
                "book__authors", "book__genres"
            )
        ]
        return ShelfBookSerializer(books, many=True).data
```

- [ ] **Step 2: Run lint + existing tests (no regressions)**

Run: `cd backend-django && uv run ruff check shelf/ && DJANGO_ENV=dev uv run python manage.py test shelf -v 1`
Expected: PASS (no new behavior tested yet; serializers import cleanly).

- [ ] **Step 3: Commit**

```bash
git add backend-django/shelf/serializers.py
git commit -m "feat(shelf): add custom-shelf serializers"
```

---

## Task 3: Owner CRUD ViewSet + routing

**Files:**
- Modify: `backend-django/shelf/views.py`
- Create: `backend-django/shelf/urls_shelves.py`
- Modify: `backend-django/config/urls.py`
- Test: `backend-django/shelf/tests/test_shelves.py`

- [ ] **Step 1: Write the failing tests**

Append to `backend-django/shelf/tests/test_shelves.py`:

```python
from rest_framework.test import APITestCase


class ShelfCrudTests(APITestCase):
    def setUp(self):
        self.alice = User.objects.create_user(email="a@x.com", handle="alice", password="pw")
        self.bob = User.objects.create_user(email="b@x.com", handle="bob", password="pw")
        self.book = Book.objects.create(title="Dune")

    def test_create_and_list_own_shelves(self):
        self.client.force_authenticate(self.alice)
        res = self.client.post("/api/shelves/", {"name": "Fantasy", "is_public": True})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["slug"], "fantasy")

        res = self.client.get("/api/shelves/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["book_count"], 0)

    def test_list_excludes_other_users_shelves(self):
        Shelf.objects.create(owner=self.bob, name="Bob Shelf")
        self.client.force_authenticate(self.alice)
        res = self.client.get("/api/shelves/")
        self.assertEqual(len(res.data), 0)

    def test_patch_updates_own_shelf(self):
        shelf = Shelf.objects.create(owner=self.alice, name="Fantasy")
        self.client.force_authenticate(self.alice)
        res = self.client.patch(f"/api/shelves/{shelf.slug}/", {"is_public": True})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data["is_public"])
        shelf.refresh_from_db()
        self.assertEqual(shelf.slug, "fantasy")  # slug stable after rename/update

    def test_cannot_patch_other_users_shelf(self):
        shelf = Shelf.objects.create(owner=self.bob, name="Bob Shelf")
        self.client.force_authenticate(self.alice)
        res = self.client.patch(f"/api/shelves/{shelf.slug}/", {"is_public": True})
        self.assertEqual(res.status_code, 404)

    def test_delete_own_shelf(self):
        shelf = Shelf.objects.create(owner=self.alice, name="Fantasy")
        self.client.force_authenticate(self.alice)
        res = self.client.delete(f"/api/shelves/{shelf.slug}/")
        self.assertEqual(res.status_code, 204)
        self.assertFalse(Shelf.objects.filter(pk=shelf.pk).exists())

    def test_duplicate_name_returns_400(self):
        Shelf.objects.create(owner=self.alice, name="Fantasy")
        self.client.force_authenticate(self.alice)
        res = self.client.post("/api/shelves/", {"name": "Fantasy"})
        self.assertEqual(res.status_code, 400)

    def test_create_requires_auth(self):
        res = self.client.post("/api/shelves/", {"name": "Fantasy"})
        self.assertEqual(res.status_code, 401)
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test shelf.tests.test_shelves.ShelfCrudTests -v 2`
Expected: FAIL — 404 (route `/api/shelves/` not registered).

- [ ] **Step 3: Add `ShelfViewSet` to `shelf/views.py`**

`shelf/views.py` already imports `OuterRef` (in `from django.db.models import OuterRef, Subquery`), `viewsets`, and `IsAuthenticated` — **do not re-import them** (ruff flags redefinition). Change the existing `django.db.models` import line to add `Count, Exists`, then add the new app imports:

```python
# change the existing line to:
from django.db.models import Count, Exists, OuterRef, Subquery

# add these:
from .models import Shelf, ShelfMembership
from .serializers import ShelfDetailSerializer, ShelfSerializer
```

Then append the ViewSet:

```python
class ShelfViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = None
    lookup_field = "slug"
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_serializer_class(self):
        return ShelfDetailSerializer if self.action == "retrieve" else ShelfSerializer

    def get_queryset(self):
        qs = (
            Shelf.objects.filter(owner=self.request.user)
            .annotate(book_count=Count("memberships"))
            .order_by("-created_at")
        )
        book_slug = self.request.query_params.get("book_slug")
        if book_slug:
            qs = qs.annotate(
                contains_book=Exists(
                    ShelfMembership.objects.filter(
                        shelf=OuterRef("pk"), book__slug=book_slug
                    )
                )
            )
        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
```

- [ ] **Step 4: Create `shelf/urls_shelves.py`**

```python
from rest_framework.routers import DefaultRouter

from .views import ShelfViewSet

router = DefaultRouter()
router.register(r"shelves", ShelfViewSet, basename="shelf")
urlpatterns = router.urls
```

- [ ] **Step 5: Register in `config/urls.py`**

In `backend-django/config/urls.py`, add after the existing `path("api/", include("reviews.urls")),` line:

```python
    path("api/", include("shelf.urls_shelves")),
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test shelf.tests.test_shelves.ShelfCrudTests -v 2`
Expected: PASS (7 tests).

- [ ] **Step 7: Commit**

```bash
git add backend-django/shelf/views.py backend-django/shelf/urls_shelves.py backend-django/config/urls.py backend-django/shelf/tests/test_shelves.py
git commit -m "feat(shelf): owner CRUD for custom shelves"
```

---

## Task 4: Membership add/remove (idempotent)

**Files:**
- Modify: `backend-django/shelf/views.py`
- Test: `backend-django/shelf/tests/test_shelves.py`

- [ ] **Step 1: Write the failing tests**

Append to `backend-django/shelf/tests/test_shelves.py`:

```python
class ShelfMembershipTests(APITestCase):
    def setUp(self):
        self.alice = User.objects.create_user(email="a@x.com", handle="alice", password="pw")
        self.bob = User.objects.create_user(email="b@x.com", handle="bob", password="pw")
        self.book = Book.objects.create(title="Dune")
        self.shelf = Shelf.objects.create(owner=self.alice, name="Fantasy")

    def test_add_book(self):
        self.client.force_authenticate(self.alice)
        res = self.client.post(
            f"/api/shelves/{self.shelf.slug}/books/", {"book_slug": self.book.slug}
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(self.shelf.memberships.count(), 1)

    def test_add_book_idempotent(self):
        self.client.force_authenticate(self.alice)
        self.client.post(f"/api/shelves/{self.shelf.slug}/books/", {"book_slug": self.book.slug})
        res = self.client.post(
            f"/api/shelves/{self.shelf.slug}/books/", {"book_slug": self.book.slug}
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.shelf.memberships.count(), 1)

    def test_add_unknown_book_404(self):
        self.client.force_authenticate(self.alice)
        res = self.client.post(f"/api/shelves/{self.shelf.slug}/books/", {"book_slug": "nope"})
        self.assertEqual(res.status_code, 404)

    def test_remove_book(self):
        ShelfMembership.objects.create(shelf=self.shelf, book=self.book)
        self.client.force_authenticate(self.alice)
        res = self.client.delete(f"/api/shelves/{self.shelf.slug}/books/{self.book.slug}/")
        self.assertEqual(res.status_code, 204)
        self.assertEqual(self.shelf.memberships.count(), 0)

    def test_remove_book_idempotent(self):
        self.client.force_authenticate(self.alice)
        res = self.client.delete(f"/api/shelves/{self.shelf.slug}/books/{self.book.slug}/")
        self.assertEqual(res.status_code, 204)

    def test_cannot_add_to_other_users_shelf(self):
        self.client.force_authenticate(self.bob)
        res = self.client.post(
            f"/api/shelves/{self.shelf.slug}/books/", {"book_slug": self.book.slug}
        )
        self.assertEqual(res.status_code, 404)

    def test_retrieve_shelf_lists_books(self):
        ShelfMembership.objects.create(shelf=self.shelf, book=self.book)
        self.client.force_authenticate(self.alice)
        res = self.client.get(f"/api/shelves/{self.shelf.slug}/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data["books"]), 1)
        self.assertEqual(res.data["books"][0]["slug"], self.book.slug)
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test shelf.tests.test_shelves.ShelfMembershipTests -v 2`
Expected: FAIL — 404 (no `books` action).

- [ ] **Step 3: Add actions to `ShelfViewSet`**

Add imports at top of `shelf/views.py` and the actions inside `ShelfViewSet`:

```python
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from books.models import Book
from .serializers import ShelfBookSerializer
```

Inside `ShelfViewSet` (after `perform_create`):

```python
    @action(detail=True, methods=["post"], url_path="books")
    def add_book(self, request, slug=None):
        shelf = self.get_object()
        book = get_object_or_404(Book, slug=request.data.get("book_slug"))
        _, created = ShelfMembership.objects.get_or_create(shelf=shelf, book=book)
        return Response(
            ShelfBookSerializer(book).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=["delete"], url_path=r"books/(?P<book_slug>[^/.]+)")
    def remove_book(self, request, slug=None, book_slug=None):
        shelf = self.get_object()
        ShelfMembership.objects.filter(shelf=shelf, book__slug=book_slug).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test shelf.tests.test_shelves.ShelfMembershipTests -v 2`
Expected: PASS (7 tests).

- [ ] **Step 5: Commit**

```bash
git add backend-django/shelf/views.py backend-django/shelf/tests/test_shelves.py
git commit -m "feat(shelf): add/remove books in custom shelf"
```

---

## Task 5: Public read endpoints

**Files:**
- Modify: `backend-django/shelf/serializers.py`
- Modify: `backend-django/shelf/views.py`
- Create: `backend-django/shelf/urls_public.py`
- Modify: `backend-django/config/urls.py`
- Test: `backend-django/shelf/tests/test_shelves.py`

- [ ] **Step 1: Write the failing tests**

Append to `backend-django/shelf/tests/test_shelves.py`:

```python
class PublicShelfTests(APITestCase):
    def setUp(self):
        self.alice = User.objects.create_user(
            email="a@x.com", handle="alice", password="pw", profile_public=True
        )
        self.book = Book.objects.create(title="Dune")
        self.public = Shelf.objects.create(owner=self.alice, name="Public", is_public=True)
        self.private = Shelf.objects.create(owner=self.alice, name="Private", is_public=False)
        ShelfMembership.objects.create(shelf=self.public, book=self.book)

    def test_public_list_returns_only_public_shelves(self):
        res = self.client.get("/api/u/alice/shelves/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["slug"], "public")

    def test_public_detail_lists_books(self):
        res = self.client.get("/api/u/alice/shelves/public/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data["books"]), 1)

    def test_private_shelf_detail_404(self):
        res = self.client.get("/api/u/alice/shelves/private/")
        self.assertEqual(res.status_code, 404)

    def test_private_profile_hides_all_shelves(self):
        self.alice.profile_public = False
        self.alice.save(update_fields=["profile_public"])
        self.assertEqual(self.client.get("/api/u/alice/shelves/").status_code, 404)
        self.assertEqual(self.client.get("/api/u/alice/shelves/public/").status_code, 404)

    def test_unknown_handle_404(self):
        self.assertEqual(self.client.get("/api/u/ghost/shelves/").status_code, 404)
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test shelf.tests.test_shelves.PublicShelfTests -v 2`
Expected: FAIL — 404 (route not registered).

- [ ] **Step 3: Add public serializers to `shelf/serializers.py`**

```python
class PublicShelfSerializer(serializers.ModelSerializer):
    book_count = serializers.SerializerMethodField()

    class Meta:
        model = Shelf
        fields = ["name", "slug", "description", "book_count", "created_at"]

    @extend_schema_field(serializers.IntegerField())
    def get_book_count(self, obj):
        count = getattr(obj, "book_count", None)
        return count if count is not None else obj.memberships.count()


class PublicShelfDetailSerializer(PublicShelfSerializer):
    books = serializers.SerializerMethodField()

    class Meta(PublicShelfSerializer.Meta):
        fields = PublicShelfSerializer.Meta.fields + ["books"]

    @extend_schema_field(ShelfBookSerializer(many=True))
    def get_books(self, obj):
        books = [
            m.book
            for m in obj.memberships.select_related("book").prefetch_related(
                "book__authors", "book__genres"
            )
        ]
        return ShelfBookSerializer(books, many=True).data
```

- [ ] **Step 4: Add public views to `shelf/views.py`**

`Count` is already imported (Task 3). Add only the new imports:

```python
from django.http import Http404
from rest_framework import generics
from rest_framework.permissions import AllowAny

from users.models import User
from .serializers import PublicShelfDetailSerializer, PublicShelfSerializer


def _public_owner_or_404(request, handle):
    owner = get_object_or_404(User, handle=handle)
    # Profile gates shelves: a private profile hides all shelves from others.
    if not owner.profile_public and owner != request.user:
        raise Http404("No User matches the given query.")
    return owner


class PublicShelfListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = PublicShelfSerializer
    pagination_class = None

    def get_queryset(self):
        owner = _public_owner_or_404(self.request, self.kwargs["handle"])
        return (
            Shelf.objects.filter(owner=owner, is_public=True)
            .annotate(book_count=Count("memberships"))
            .order_by("-created_at")
        )


class PublicShelfDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = PublicShelfDetailSerializer

    def get_object(self):
        owner = _public_owner_or_404(self.request, self.kwargs["handle"])
        return get_object_or_404(
            Shelf, owner=owner, slug=self.kwargs["slug"], is_public=True
        )
```

- [ ] **Step 5: Create `shelf/urls_public.py`**

```python
from django.urls import path

from .views import PublicShelfDetailView, PublicShelfListView

urlpatterns = [
    path("", PublicShelfListView.as_view(), name="public-shelf-list"),
    path("<slug:slug>/", PublicShelfDetailView.as_view(), name="public-shelf-detail"),
]
```

- [ ] **Step 6: Register in `config/urls.py`**

In `backend-django/config/urls.py`, add after the existing `path("api/u/", include("users.urls.public")),` line:

```python
    path("api/u/<str:handle>/shelves/", include("shelf.urls_public")),
```

(The `api/u/` profile include only matches a single `<handle>/` segment, so `api/u/{handle}/shelves/...` falls through to this more specific pattern.)

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test shelf.tests.test_shelves.PublicShelfTests -v 2`
Expected: PASS (5 tests).

- [ ] **Step 8: Commit**

```bash
git add backend-django/shelf/serializers.py backend-django/shelf/views.py backend-django/shelf/urls_public.py backend-django/config/urls.py backend-django/shelf/tests/test_shelves.py
git commit -m "feat(shelf): public read for custom shelves"
```

---

## Task 6: Add shelves to data export

**Files:**
- Modify: `backend-django/users/exporters.py`
- Test: `backend-django/users/tests/` (existing export test file — find with grep below)

- [ ] **Step 1: Locate the export test**

Run: `cd backend-django && grep -rl "shelf_entries.json\|build_user_export_zip\|README.txt" users/tests/`
Use the file it prints as the export test file in the next step.

- [ ] **Step 2: Write the failing test**

Add to the export test file found above (mirror the style of the existing `shelf_entries.json` assertion in that file):

```python
    def test_export_includes_shelves(self):
        from shelf.models import Shelf, ShelfMembership

        shelf = Shelf.objects.create(owner=self.user, name="Fantasy", is_public=True)
        book = Book.objects.create(title="Dune")
        ShelfMembership.objects.create(shelf=shelf, book=book)

        data = build_user_export_zip(self.user)
        import io
        import json
        import zipfile

        zf = zipfile.ZipFile(io.BytesIO(data))
        shelves = json.loads(zf.read("shelves.json"))
        self.assertEqual(len(shelves), 1)
        self.assertEqual(shelves[0]["name"], "Fantasy")
        self.assertEqual(shelves[0]["books"], ["dune"])
```

> If `self.user` / `Book` imports differ in that test file, match its existing setUp conventions.

- [ ] **Step 3: Run to verify failure**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test users -v 2 -k shelves`
Expected: FAIL — `KeyError: "There is no item named 'shelves.json'"`.

- [ ] **Step 4: Add `shelves.json` to `users/exporters.py`**

In `build_user_export_zip`, after the `reviews.json` block, add:

```python
        # shelves.json
        shelves_qs = user.shelves.prefetch_related("memberships__book").order_by("-created_at")
        shelves_data = [
            {
                "name": s.name,
                "slug": s.slug,
                "description": s.description,
                "is_public": s.is_public,
                "created_at": s.created_at,
                "books": [m.book.slug for m in s.memberships.all()],
            }
            for s in shelves_qs
        ]
        zf.writestr("shelves.json", json.dumps(shelves_data, indent=2, cls=_DatetimeEncoder))
```

And add one line to the README block (after the `reviews.json` line):

```python
            f"  shelves.json       — custom shelves and their books\n"
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test users -v 1`
Expected: PASS (all export tests, incl. new one).

- [ ] **Step 6: Commit**

```bash
git add backend-django/users/exporters.py backend-django/users/tests/
git commit -m "feat(users): include shelves in data export"
```

---

## Task 7: OpenAPI contract regen

**Files:**
- Modify: `docs/api/openapi.yml` (regenerated)

- [ ] **Step 1: Regenerate the schema**

Run: `cd backend-django && make regenerate-openapi`
(If the target is defined at repo root, run `make regenerate-openapi` from the repo root instead — check `Makefile` for the target.)
Expected: `docs/api/openapi.yml` updated with `/api/shelves/...` and `/api/u/{handle}/shelves/...` paths.

- [ ] **Step 2: Run the contract test**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test config.tests.test_openapi_schema -v 2`
Expected: PASS (live schema matches committed `openapi.yml`).

- [ ] **Step 3: Run the full backend suite (regression gate)**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test`
Expected: PASS (all tests green).

- [ ] **Step 4: Commit**

```bash
git add docs/api/openapi.yml
git commit -m "docs(api): regenerate schema for shelves"
```

---

## Task 8: Frontend types + API client

**Files:**
- Modify: `svelte-frontend/src/lib/types/shelf.ts`
- Create: `svelte-frontend/src/lib/api/shelves.ts`

- [ ] **Step 1: Add types to `lib/types/shelf.ts`**

Append to `svelte-frontend/src/lib/types/shelf.ts` (`ShelfBook` już istnieje — reuse):

```typescript
export interface Shelf {
	id: number;
	name: string;
	slug: string;
	description: string;
	is_public: boolean;
	book_count: number;
	/** Present only when the list is fetched with a bookSlug filter; else null. */
	contains_book: boolean | null;
	created_at: string;
	updated_at: string;
}

export interface ShelfDetail extends Shelf {
	books: ShelfBook[];
}

export interface PublicShelf {
	name: string;
	slug: string;
	description: string;
	book_count: number;
	created_at: string;
}

export interface PublicShelfDetail extends PublicShelf {
	books: ShelfBook[];
}

export interface ShelfCreate {
	name: string;
	description?: string;
	is_public?: boolean;
}

export interface ShelfUpdate {
	name?: string;
	description?: string;
	is_public?: boolean;
}
```

- [ ] **Step 2: Create `lib/api/shelves.ts`**

```typescript
import { apiFetch } from './_client';
import type {
	Shelf,
	ShelfDetail,
	ShelfCreate,
	ShelfUpdate,
	PublicShelf,
	PublicShelfDetail,
	ShelfBook
} from '$lib/types/shelf';

/** Current user's custom shelves. Pass bookSlug to get `contains_book` per shelf. */
export function fetchMyShelves(fetchFn: typeof fetch, bookSlug?: string, isServerSide = false) {
	const q = bookSlug ? `?book_slug=${encodeURIComponent(bookSlug)}` : '';
	return apiFetch<Shelf[]>(fetchFn, `/shelves/${q}`, undefined, isServerSide);
}

export function fetchMyShelf(fetchFn: typeof fetch, slug: string, isServerSide = false) {
	return apiFetch<ShelfDetail>(fetchFn, `/shelves/${slug}/`, undefined, isServerSide);
}

export function createShelf(fetchFn: typeof fetch, data: ShelfCreate) {
	return apiFetch<Shelf>(fetchFn, '/shelves/', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

export function updateShelf(fetchFn: typeof fetch, slug: string, data: ShelfUpdate) {
	return apiFetch<Shelf>(fetchFn, `/shelves/${slug}/`, {
		method: 'PATCH',
		body: JSON.stringify(data)
	});
}

export function deleteShelf(fetchFn: typeof fetch, slug: string) {
	return apiFetch<null>(fetchFn, `/shelves/${slug}/`, { method: 'DELETE' });
}

export function addBookToShelf(fetchFn: typeof fetch, slug: string, bookSlug: string) {
	return apiFetch<ShelfBook>(fetchFn, `/shelves/${slug}/books/`, {
		method: 'POST',
		body: JSON.stringify({ book_slug: bookSlug })
	});
}

export function removeBookFromShelf(fetchFn: typeof fetch, slug: string, bookSlug: string) {
	return apiFetch<null>(fetchFn, `/shelves/${slug}/books/${bookSlug}/`, { method: 'DELETE' });
}

/** Public shelves of a user (by handle). */
export function fetchPublicShelves(fetchFn: typeof fetch, handle: string, isServerSide = false) {
	return apiFetch<PublicShelf[]>(fetchFn, `/u/${handle}/shelves/`, undefined, isServerSide);
}

export function fetchPublicShelf(
	fetchFn: typeof fetch,
	handle: string,
	slug: string,
	isServerSide = false
) {
	return apiFetch<PublicShelfDetail>(
		fetchFn,
		`/u/${handle}/shelves/${slug}/`,
		undefined,
		isServerSide
	);
}
```

- [ ] **Step 3: Type-check**

Run: `cd svelte-frontend && npm run check`
Expected: PASS (no type errors).

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/src/lib/types/shelf.ts svelte-frontend/src/lib/api/shelves.ts
git commit -m "feat(web): shelves API client + types"
```

---

## Task 9: /shelf — "Moje półki" tab (list + create)

**Files:**
- Modify: `svelte-frontend/src/routes/shelf/+page.server.ts`
- Modify: `svelte-frontend/src/routes/shelf/+page.svelte`

- [ ] **Step 1: Load shelves in `+page.server.ts`**

Modify `svelte-frontend/src/routes/shelf/+page.server.ts` to also fetch shelves. Add import and extend the `Promise.all` + return:

```typescript
import { fetchMyShelves } from '$lib/api/shelves';
```

Add `fetchMyShelves(fetch, undefined, true)` to the `Promise.all` array (capture as `shelvesRes`), and add to the returned object:

```typescript
	return { entries, shelves: shelvesRes.data ?? [] };
```

- [ ] **Step 2: Add tabs + create form to `+page.svelte`**

In `svelte-frontend/src/routes/shelf/+page.svelte`, follow the existing page's component/styling conventions. Add reactive tab state and a "Moje półki" panel. Core logic (Svelte 5 runes):

```svelte
<script lang="ts">
	import { invalidateAll } from '$app/navigation';
	import { createShelf } from '$lib/api/shelves';
	import type { Shelf } from '$lib/types/shelf';

	let { data } = $props();
	let tab = $state<'status' | 'shelves'>('status');
	let shelves = $state<Shelf[]>(data.shelves);
	$effect(() => { shelves = data.shelves; });

	let newName = $state('');
	let newPublic = $state(false);
	let creating = $state(false);
	let createError = $state('');

	async function handleCreate() {
		if (!newName.trim()) return;
		creating = true;
		createError = '';
		const { error } = await createShelf(fetch, { name: newName.trim(), is_public: newPublic });
		creating = false;
		if (error) { createError = error.detail; return; }
		newName = '';
		newPublic = false;
		await invalidateAll();
	}
</script>

<div class="tabs">
	<button class:active={tab === 'status'} onclick={() => (tab = 'status')}>Status czytania</button>
	<button class:active={tab === 'shelves'} onclick={() => (tab = 'shelves')}>Moje półki</button>
</div>

{#if tab === 'status'}
	<!-- existing reading-status markup stays here, unchanged -->
{:else}
	<form onsubmit={(e) => { e.preventDefault(); handleCreate(); }}>
		<input bind:value={newName} placeholder="Nazwa półki" maxlength="100" />
		<label><input type="checkbox" bind:checked={newPublic} /> Publiczna</label>
		<button type="submit" disabled={creating}>Utwórz</button>
		{#if createError}<p class="error">{createError}</p>{/if}
	</form>

	<ul class="shelf-list">
		{#each shelves as shelf (shelf.id)}
			<li>
				<a href="/shelf/{shelf.slug}">{shelf.name}</a>
				<span>{shelf.book_count} książek</span>
				{#if shelf.is_public}<span class="badge">Publiczna</span>{/if}
			</li>
		{/each}
		{#if shelves.length === 0}<li class="empty">Brak półek. Utwórz pierwszą.</li>{/if}
	</ul>
{/if}
```

> Wrap the EXISTING reading-status markup in the `{#if tab === 'status'}` branch — don't delete it. Match existing Tailwind classes used elsewhere on the page for the new elements.

- [ ] **Step 3: Type-check + lint**

Run: `cd svelte-frontend && npm run check && npm run lint`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/src/routes/shelf/+page.server.ts svelte-frontend/src/routes/shelf/+page.svelte
git commit -m "feat(web): My Shelves tab on /shelf"
```

---

## Task 10: /shelf/[slug] — own shelf view (edit, remove books)

**Files:**
- Create: `svelte-frontend/src/routes/shelf/[slug]/+page.server.ts`
- Create: `svelte-frontend/src/routes/shelf/[slug]/+page.svelte`

> Note: `/shelf/[slug]` inherits `/shelf/+layout.server.ts` (auth redirect for guests), so the page is owner-only by construction.

- [ ] **Step 1: Create `+page.server.ts`**

```typescript
import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { fetchMyShelf } from '$lib/api/shelves';

export const load: PageServerLoad = async ({ fetch, params }) => {
	const { data, error: err } = await fetchMyShelf(fetch, params.slug, true);
	if (err) {
		throw error(err.status === 404 ? 404 : 500, err.detail || 'Failed to load shelf');
	}
	return { shelf: data! };
};
```

- [ ] **Step 2: Create `+page.svelte`**

```svelte
<script lang="ts">
	import { goto, invalidateAll } from '$app/navigation';
	import { updateShelf, deleteShelf, removeBookFromShelf } from '$lib/api/shelves';
	import type { ShelfDetail } from '$lib/types/shelf';

	let { data } = $props();
	let shelf = $state<ShelfDetail>(data.shelf);
	$effect(() => { shelf = data.shelf; });

	let name = $state(data.shelf.name);
	let description = $state(data.shelf.description);
	let isPublic = $state(data.shelf.is_public);
	let saving = $state(false);
	let saveError = $state('');

	async function save() {
		saving = true;
		saveError = '';
		const { error } = await updateShelf(fetch, shelf.slug, {
			name: name.trim(),
			description,
			is_public: isPublic
		});
		saving = false;
		if (error) { saveError = error.detail; return; }
		await invalidateAll();
	}

	async function remove(bookSlug: string) {
		const { error } = await removeBookFromShelf(fetch, shelf.slug, bookSlug);
		if (!error) await invalidateAll();
	}

	async function destroy() {
		if (!confirm(`Usunąć półkę "${shelf.name}"?`)) return;
		const { error } = await deleteShelf(fetch, shelf.slug);
		if (!error) await goto('/shelf');
	}
</script>

<h1>{shelf.name}</h1>

<form onsubmit={(e) => { e.preventDefault(); save(); }}>
	<input bind:value={name} maxlength="100" />
	<textarea bind:value={description}></textarea>
	<label><input type="checkbox" bind:checked={isPublic} /> Publiczna</label>
	<button type="submit" disabled={saving}>Zapisz</button>
	{#if saveError}<p class="error">{saveError}</p>{/if}
</form>

<button class="danger" onclick={destroy}>Usuń półkę</button>

<ul class="book-grid">
	{#each shelf.books as book (book.slug)}
		<li>
			<a href="/books/{book.slug}">{book.title}</a>
			<button onclick={() => remove(book.slug)}>Usuń z półki</button>
		</li>
	{/each}
	{#if shelf.books.length === 0}<li class="empty">Półka jest pusta.</li>{/if}
</ul>
```

> Reuse the existing book-card component/markup used on `/discover` or `/shelf` for `book-grid` items if one exists; keep the remove button.

- [ ] **Step 3: Type-check + lint**

Run: `cd svelte-frontend && npm run check && npm run lint`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/src/routes/shelf/\[slug\]/
git commit -m "feat(web): own shelf detail view"
```

---

## Task 11: /books/[slug] — "Add to shelf" control

**Files:**
- Modify: `svelte-frontend/src/routes/books/[slug]/+page.server.ts`
- Modify: `svelte-frontend/src/routes/books/[slug]/+page.svelte`

- [ ] **Step 1: Load my shelves (with membership flag) in `+page.server.ts`**

In `svelte-frontend/src/routes/books/[slug]/+page.server.ts`:

Add import:

```typescript
import { fetchMyShelves } from '$lib/api/shelves';
```

Add to the `Promise.all` array (guarded by `user`, like the other authed calls):

```typescript
		user
			? fetchMyShelves(fetch, params.slug, true)
			: Promise.resolve({ data: null, error: null })
```

Capture it as `myShelvesRes` and add to the return object:

```typescript
		myShelves: myShelvesRes.data ?? []
```

- [ ] **Step 2: Add the control to `+page.svelte`**

In `svelte-frontend/src/routes/books/[slug]/+page.svelte`, add a "Dodaj do półki" dropdown shown only when `data.user`. Use the existing `DropdownMenu` component if the page already uses one; otherwise a simple `<details>`.

> GOTCHA (see project memory): a custom `DropdownMenu` unmounts its content on close — wire toggles via synchronous `onclick`, never a native form submit.

Core logic:

```svelte
<script lang="ts">
	import { addBookToShelf, removeBookFromShelf } from '$lib/api/shelves';
	import type { Shelf } from '$lib/types/shelf';

	// ... existing props ...
	let myShelves = $state<Shelf[]>(data.myShelves);
	$effect(() => { myShelves = data.myShelves; });

	async function toggle(shelf: Shelf) {
		const wasIn = shelf.contains_book === true;
		const call = wasIn
			? removeBookFromShelf(fetch, shelf.slug, data.book.slug)
			: addBookToShelf(fetch, shelf.slug, data.book.slug);
		const { error } = await call;
		if (!error) {
			// Update in place so the checkbox reflects the new state.
			myShelves = myShelves.map((s) =>
				s.id === shelf.id
					? { ...s, contains_book: !wasIn, book_count: s.book_count + (wasIn ? -1 : 1) }
					: s
			);
		}
	}
</script>

{#if data.user}
	<details class="add-to-shelf">
		<summary>Dodaj do półki</summary>
		<ul>
			{#each myShelves as shelf (shelf.id)}
				<li>
					<label>
						<input type="checkbox" checked={shelf.contains_book === true} onclick={() => toggle(shelf)} />
						{shelf.name}
					</label>
				</li>
			{/each}
			{#if myShelves.length === 0}
				<li><a href="/shelf">Utwórz pierwszą półkę</a></li>
			{/if}
		</ul>
	</details>
{/if}
```

> `$state` (not `$derived`) for `myShelves` because we mutate it in place — see project memory on the `$derived` in-place gotcha. Place this control near the existing shelf-status / rating controls; match their styling.

- [ ] **Step 3: Type-check + lint**

Run: `cd svelte-frontend && npm run check && npm run lint`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/src/routes/books/\[slug\]/
git commit -m "feat(web): add-to-shelf control on book page"
```

---

## Task 12: /u/[handle] — public shelves list

**Files:**
- Modify: `svelte-frontend/src/routes/u/[handle]/+page.server.ts`
- Modify: `svelte-frontend/src/routes/u/[handle]/+page.svelte`

- [ ] **Step 1: Load public shelves in `+page.server.ts`**

In `svelte-frontend/src/routes/u/[handle]/+page.server.ts`, add import and fetch (after the profile is resolved, so a 404 profile still short-circuits):

```typescript
import { fetchPublicShelves } from '$lib/api/shelves';
```

After the existing profile resolution and before `return`:

```typescript
	const { data: shelves } = await fetchPublicShelves(fetch, params.handle, true);
```

Add to the return object: `shelves: shelves ?? []`.

- [ ] **Step 2: Render the list in `+page.svelte`**

Add a section listing public shelves (each links to `/u/{handle}/shelves/{slug}`):

```svelte
<script lang="ts">
	// ... existing ...
	import type { PublicShelf } from '$lib/types/shelf';
	let shelves = $derived(data.shelves as PublicShelf[]);
</script>

{#if shelves.length > 0}
	<section class="public-shelves">
		<h2>Półki</h2>
		<ul>
			{#each shelves as shelf (shelf.slug)}
				<li>
					<a href="/u/{data.profile.handle}/shelves/{shelf.slug}">{shelf.name}</a>
					<span>{shelf.book_count} książek</span>
				</li>
			{/each}
		</ul>
	</section>
{/if}
```

> `$derived` is fine here — `shelves` is only ever reassigned from `data`, never mutated in place.

- [ ] **Step 3: Type-check + lint**

Run: `cd svelte-frontend && npm run check && npm run lint`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/src/routes/u/\[handle\]/+page.server.ts svelte-frontend/src/routes/u/\[handle\]/+page.svelte
git commit -m "feat(web): public shelves on profile"
```

---

## Task 13: /u/[handle]/shelves/[slug] — public shelf view

**Files:**
- Create: `svelte-frontend/src/routes/u/[handle]/shelves/[slug]/+page.server.ts`
- Create: `svelte-frontend/src/routes/u/[handle]/shelves/[slug]/+page.svelte`

- [ ] **Step 1: Create `+page.server.ts`**

```typescript
import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { fetchPublicShelf } from '$lib/api/shelves';

export const load: PageServerLoad = async ({ fetch, params }) => {
	const { data, error: err } = await fetchPublicShelf(fetch, params.handle, params.slug, true);
	if (err) {
		throw error(err.status === 404 ? 404 : 500, err.detail || 'Failed to load shelf');
	}
	return { shelf: data!, handle: params.handle };
};
```

- [ ] **Step 2: Create `+page.svelte`**

```svelte
<script lang="ts">
	import type { PublicShelfDetail } from '$lib/types/shelf';
	let { data } = $props();
	let shelf = $derived(data.shelf as PublicShelfDetail);
</script>

<a href="/u/{data.handle}">← {data.handle}</a>
<h1>{shelf.name}</h1>
{#if shelf.description}<p>{shelf.description}</p>{/if}

<ul class="book-grid">
	{#each shelf.books as book (book.slug)}
		<li><a href="/books/{book.slug}">{book.title}</a></li>
	{/each}
	{#if shelf.books.length === 0}<li class="empty">Półka jest pusta.</li>{/if}
</ul>
```

> Reuse the shared book-card component used on `/discover` for grid items if one exists.

- [ ] **Step 3: Type-check + lint**

Run: `cd svelte-frontend && npm run check && npm run lint`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/src/routes/u/\[handle\]/shelves/
git commit -m "feat(web): public shelf detail page"
```

---

## Task 14: E2E scenarios

**Files:**
- Create: `svelte-frontend/e2e/shelves.spec.ts`

> Read an existing spec first (e.g. `svelte-frontend/e2e/*.spec.ts`) to reuse the project's auth/seed helpers and `global-setup` conventions (E2E seeds via API). GOTCHA (project memory): register throttle 5/h can block full suites; the hydration race in dev needs retry-click `toPass`. Reuse existing login helper rather than registering fresh users where possible.

- [ ] **Step 1: Write the E2E spec (mirror existing spec structure/helpers)**

Create `svelte-frontend/e2e/shelves.spec.ts` with 4 scenarios, using the project's existing helpers (replace `loginAs` / selectors with whatever the existing specs use):

```typescript
import { test, expect } from '@playwright/test';
// import the project's existing auth/seed helpers here, matching other specs

test.describe('Custom shelves', () => {
	test('create shelf and add a book from book page', async ({ page }) => {
		// log in (existing helper)
		await page.goto('/shelf');
		await page.getByRole('button', { name: 'Moje półki' }).click();
		await page.getByPlaceholder('Nazwa półki').fill('My Fantasy');
		await page.getByRole('button', { name: 'Utwórz' }).click();
		await expect(page.getByText('My Fantasy')).toBeVisible();

		// add a book to the shelf from a book page (use a seeded book slug)
		await page.goto('/books/<seeded-book-slug>');
		await page.getByText('Dodaj do półki').click();
		await page.getByLabel('My Fantasy').check();

		await page.goto('/shelf');
		await page.getByRole('button', { name: 'Moje półki' }).click();
		await expect(page.getByText('1 książek')).toBeVisible();
	});

	test('public shelf is visible to a guest', async ({ page, browser }) => {
		// owner: create shelf, set public, add a book (UI or seed)
		// guest (new context, no auth): visit /u/<handle>/shelves/<slug> → shelf visible
	});

	test('private shelf is hidden from a guest', async ({ browser }) => {
		// guest visits /u/<handle>/shelves/<private-slug> → 404 page
	});

	test('delete shelf removes it from My Shelves', async ({ page }) => {
		// create shelf, open /shelf/<slug>, confirm delete → redirected to /shelf, gone
	});
});
```

> Fill the placeholder helpers/slugs from the existing specs — do not leave `<seeded-book-slug>` / `<handle>` literal. The 4 scenarios map to spec section "E2E".

- [ ] **Step 2: Run E2E**

Run: `cd svelte-frontend && npx playwright test shelves.spec.ts`
Expected: PASS (4 scenarios). If hydration flakiness appears, wrap the failing click in Playwright `expect.poll`/`toPass` per the project gotcha.

- [ ] **Step 3: Commit**

```bash
git add svelte-frontend/e2e/shelves.spec.ts
git commit -m "test(e2e): custom shelves scenarios"
```

---

## Final verification

- [ ] **Backend full suite:** `cd backend-django && DJANGO_ENV=dev uv run python manage.py test` → all green.
- [ ] **Backend lint:** `cd backend-django && uv run ruff check .` → clean.
- [ ] **Frontend:** `cd svelte-frontend && npm run check && npm run lint` → clean.
- [ ] **E2E:** `cd svelte-frontend && npx playwright test` → green.
- [ ] **OpenAPI contract:** confirmed in Task 7.
- [ ] Update `docs/ROADMAP.md`: move M5 from "Następne" to "Zrobione" (do this on the roadmap-fix branch or here per workflow).
- [ ] `/requesting-code-review` → fixes → `/finishing-a-development-branch`.
```
