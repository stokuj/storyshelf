# M12 — Social feed + reakcje Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an activity feed of followed users, review likes, and public reviews on profiles.

**Architecture:** Feed is computed on-the-fly by merging `Rating`/`Review`/`ShelfEntry(READ)` rows from followed public users (no `Activity` model). Review likes via a new `ReviewLike` model + idempotent action. Public reviews via a gated list view. Frontend adds `/feed`, a like control on `ReviewCard`, and a Reviews section on the profile.

**Tech Stack:** Django 6 + DRF (backend, `uv`, tests need `DJANGO_ENV=dev`), SvelteKit 2 + Svelte 5 (frontend), Playwright (E2E).

**Conventions:**
- Backend tests: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test <path>`
- Dev DB model changes: `DJANGO_ENV=dev uv run python manage.py makemigrations && migrate` (reset DB if needed: `flush --no-input && migrate`)
- Commit style: `feat:` / `test:` / `docs:` (conventional, title ≤ 50 chars)
- Frontend checks: `cd svelte-frontend && npm run check && npm run lint`

---

## File Structure

**Backend (`backend-django/`):**
- `shelf/models.py` — add `ShelfEntry.updated_at`
- `reviews/models.py` — add `ReviewLike`
- `reviews/serializers.py` — add `likes_count` + `is_liked` to `ReviewSerializer`
- `reviews/views.py` — `like` action, `annotate_reviews()` helper, `UserReviewListView`
- `reviews/urls.py` — register `reviews/<pk>/like/`
- `reviews/tests/test_models.py`, `reviews/tests/test_api.py` — ReviewLike + public reviews tests
- `feed/` (new app) — `views.py`, `serializers.py`, `apps.py`, `__init__.py`, `urls.py`, `tests/`
- `config/urls.py` — register feed + public reviews routes
- `config/settings/` — add `feed` to `INSTALLED_APPS`

**Frontend (`svelte-frontend/`):**
- `src/lib/types/review.ts` — add `likes_count`, `is_liked`
- `src/lib/types/feed.ts` (new) — feed item types
- `src/lib/api/reviews.ts` — `likeReview`, `unlikeReview`, `fetchUserReviews`
- `src/lib/api/feed.ts` (new) — `fetchFeed`
- `src/lib/components/review/ReviewCard.svelte` — like control
- `src/lib/components/feed/FeedItem.svelte` (new)
- `src/routes/feed/+page.server.ts`, `+page.svelte` (new)
- `src/routes/u/[handle]/+page.server.ts`, `+page.svelte` — Reviews section
- `src/lib/components/shell/AppShell.svelte` — Feed nav link
- `e2e/tests/social-feed.spec.ts` (new)

---

## Task 1: Add `ShelfEntry.updated_at`

**Files:**
- Modify: `backend-django/shelf/models.py`
- Test: `backend-django/shelf/tests/test_models.py` (or existing shelf model test file)

- [ ] **Step 1: Write the failing test**

Find the shelf model test file (`ls backend-django/shelf/tests/`). Add to the `ShelfEntry` model test class:

```python
def test_shelfentry_has_updated_at(self):
    entry = ShelfEntry.objects.create(user=self.user, book=self.book)
    self.assertIsNotNone(entry.updated_at)
```

(Ensure `self.user` / `self.book` exist in that class's `setUpTestData`; mirror an existing test's fixtures.)

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test shelf.tests.test_models -v 2`
Expected: FAIL — `AttributeError: 'ShelfEntry' object has no attribute 'updated_at'`

- [ ] **Step 3: Add the field**

In `shelf/models.py`, in `ShelfEntry`, right after `created_at`:

```python
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

- [ ] **Step 4: Make + apply migration**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py makemigrations shelf && DJANGO_ENV=dev uv run python manage.py migrate`
Expected: new migration created and applied.

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test shelf.tests.test_models -v 2`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend-django/shelf/models.py backend-django/shelf/migrations/ backend-django/shelf/tests/test_models.py
git commit -m "feat: add ShelfEntry.updated_at for feed sorting"
```

---

## Task 2: `ReviewLike` model

**Files:**
- Modify: `backend-django/reviews/models.py`
- Test: `backend-django/reviews/tests/test_models.py`

- [ ] **Step 1: Write the failing test**

Append to `reviews/tests/test_models.py`:

```python
from django.db import IntegrityError
from reviews.models import ReviewLike


class ReviewLikeModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="liker@test.com", handle="liker", password="password123"
        )
        cls.book = Book.objects.create(title="Likeable", slug="likeable")
        cls.review = Review.objects.create(user=cls.user, book=cls.book, body="Nice")

    def test_one_like_per_user_review(self):
        ReviewLike.objects.create(user=self.user, review=self.review)
        with self.assertRaises(IntegrityError):
            ReviewLike.objects.create(user=self.user, review=self.review)

    def test_user_can_like_own_review(self):
        like = ReviewLike.objects.create(user=self.user, review=self.review)
        self.assertEqual(like.review, self.review)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test reviews.tests.test_models -v 2`
Expected: FAIL — `ImportError: cannot import name 'ReviewLike'`

- [ ] **Step 3: Add the model**

In `reviews/models.py`, append after `Review`:

```python
class ReviewLike(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="review_likes",
        db_index=True,
    )
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="likes",
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "review"], name="unique_user_review_like"),
        ]

    def __str__(self):
        return f"{self.user.handle} ♥ review#{self.review_id}"
```

- [ ] **Step 4: Make + apply migration**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py makemigrations reviews && DJANGO_ENV=dev uv run python manage.py migrate`
Expected: new migration created and applied.

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test reviews.tests.test_models -v 2`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend-django/reviews/models.py backend-django/reviews/migrations/ backend-django/reviews/tests/test_models.py
git commit -m "feat: add ReviewLike model"
```

---

## Task 3: Like/unlike endpoint

**Files:**
- Modify: `backend-django/reviews/views.py`, `backend-django/reviews/urls.py`
- Test: `backend-django/reviews/tests/test_api.py`

- [ ] **Step 1: Write the failing test**

Append to `reviews/tests/test_api.py`:

```python
class ReviewLikeAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(
            email="auth@test.com", handle="author", password="password123"
        )
        cls.liker = User.objects.create_user(
            email="lk@test.com", handle="lk", password="password123"
        )
        cls.book = Book.objects.create(title="B", slug="b")
        cls.review = Review.objects.create(user=cls.author, book=cls.book, body="hello")

    def _url(self):
        return f"/api/reviews/{self.review.id}/like/"

    def test_post_like_returns_count_and_flag(self):
        self.client.force_authenticate(self.liker)
        resp = self.client.post(self._url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, {"likes_count": 1, "is_liked": True})

    def test_post_like_is_idempotent(self):
        self.client.force_authenticate(self.liker)
        self.client.post(self._url())
        resp = self.client.post(self._url())
        self.assertEqual(resp.data["likes_count"], 1)

    def test_delete_unlike(self):
        self.client.force_authenticate(self.liker)
        self.client.post(self._url())
        resp = self.client.delete(self._url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, {"likes_count": 0, "is_liked": False})

    def test_delete_when_not_liked_is_idempotent(self):
        self.client.force_authenticate(self.liker)
        resp = self.client.delete(self._url())
        self.assertEqual(resp.data, {"likes_count": 0, "is_liked": False})

    def test_like_requires_auth(self):
        resp = self.client.post(self._url())
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_like_unknown_review_404(self):
        self.client.force_authenticate(self.liker)
        resp = self.client.post("/api/reviews/99999/like/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test reviews.tests.test_api.ReviewLikeAPITest -v 2`
Expected: FAIL — 404 (route not registered).

- [ ] **Step 3: Add the action**

In `reviews/views.py`, update imports at top:

```python
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Review, ReviewLike
```

Add this action inside `ReviewViewSet` (after `me`):

```python
    @action(detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        review = get_object_or_404(Review, pk=pk)
        if request.method == "POST":
            ReviewLike.objects.get_or_create(user=request.user, review=review)
            is_liked = True
        else:
            ReviewLike.objects.filter(user=request.user, review=review).delete()
            is_liked = False
        return Response({"likes_count": review.likes.count(), "is_liked": is_liked})
```

- [ ] **Step 4: Register the route**

In `reviews/urls.py`, add before `reviews/<int:pk>/`:

```python
    path(
        "reviews/<int:pk>/like/",
        ReviewViewSet.as_view({"post": "like", "delete": "like"}),
        name="review-like",
    ),
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test reviews.tests.test_api.ReviewLikeAPITest -v 2`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend-django/reviews/views.py backend-django/reviews/urls.py backend-django/reviews/tests/test_api.py
git commit -m "feat: add review like/unlike endpoint"
```

---

## Task 4: `likes_count` + `is_liked` on `ReviewSerializer`

**Files:**
- Modify: `backend-django/reviews/serializers.py`, `backend-django/reviews/views.py`
- Test: `backend-django/reviews/tests/test_api.py`

- [ ] **Step 1: Write the failing test**

Append to `reviews/tests/test_api.py` (inside `ReviewLikeAPITest` or a new method group reusing its fixtures):

```python
    def test_list_includes_likes_count_and_is_liked(self):
        ReviewLike.objects.create(user=self.liker, review=self.review)
        self.client.force_authenticate(self.liker)
        resp = self.client.get("/api/reviews/?book_slug=b")
        row = resp.data["data"][0]
        self.assertEqual(row["likes_count"], 1)
        self.assertTrue(row["is_liked"])

    def test_list_anon_is_liked_false(self):
        ReviewLike.objects.create(user=self.liker, review=self.review)
        resp = self.client.get("/api/reviews/?book_slug=b")
        row = resp.data["data"][0]
        self.assertEqual(row["likes_count"], 1)
        self.assertFalse(row["is_liked"])
```

(Add `from reviews.models import Review, ReviewLike` at the top of the test file if not present.)

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test reviews.tests.test_api.ReviewLikeAPITest -v 2`
Expected: FAIL — `KeyError: 'likes_count'`

- [ ] **Step 3: Add serializer fields**

In `reviews/serializers.py`, import the model and add two fields:

```python
from .models import Review, ReviewLike
```

In `ReviewSerializer`, add fields (after `author_rating = serializers.SerializerMethodField()`):

```python
    likes_count = serializers.IntegerField(read_only=True, default=0)
    is_liked = serializers.BooleanField(read_only=True, default=False)
```

Add both to `Meta.fields` and `Meta.read_only_fields`:

```python
        fields = [
            "id",
            "book_slug",
            "body",
            "author",
            "author_rating",
            "likes_count",
            "is_liked",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", "author", "author_rating", "likes_count", "is_liked",
            "created_at", "updated_at",
        ]
```

(`ReviewLike` import is unused in the serializer for now — remove it if `ruff` flags it; it is referenced by the view helper instead. Prefer importing it only where used.)

- [ ] **Step 4: Add annotation helper + wire into view queryset**

In `reviews/views.py`, add imports:

```python
from django.db.models import Count, Exists, OuterRef, Subquery
```

Add a module-level helper (after imports, before `ReviewViewSet`):

```python
def annotate_reviews(qs, user):
    """Attach author_rating, likes_count, is_liked to a Review queryset."""
    author_rating = Rating.objects.filter(
        user=OuterRef("user"), book=OuterRef("book")
    ).values("rating")[:1]
    qs = qs.annotate(
        author_rating=Subquery(author_rating),
        likes_count=Count("likes", distinct=True),
    ).select_related("user", "book")
    if user.is_authenticated:
        qs = qs.annotate(
            is_liked=Exists(ReviewLike.objects.filter(review=OuterRef("pk"), user=user))
        )
    return qs
```

Replace the body of `ReviewViewSet.get_queryset` so it uses the helper:

```python
    def get_queryset(self):
        qs = annotate_reviews(Review.objects.all(), self.request.user).order_by("-created_at")
        if self.action == "destroy":
            qs = qs.filter(user=self.request.user)
        book_slug = self.request.query_params.get("book_slug")
        if book_slug:
            qs = qs.filter(book__slug=book_slug)
        return qs
```

Remove the now-unused inline `author_rating`/`OuterRef`/`Subquery` block from the old `get_queryset` body (the helper owns it). Keep the existing `update`/`me` methods unchanged — they already call `self.get_queryset()`.

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test reviews.tests.test_api -v 2`
Expected: PASS (all review API tests, including pre-existing ones).

- [ ] **Step 6: Lint + commit**

```bash
cd backend-django && uv run ruff check --fix . && cd ..
git add backend-django/reviews/serializers.py backend-django/reviews/views.py backend-django/reviews/tests/test_api.py
git commit -m "feat: expose likes_count and is_liked on reviews"
```

---

## Task 5: Public reviews endpoint `GET /api/u/{handle}/reviews/`

**Files:**
- Modify: `backend-django/reviews/views.py`, `backend-django/config/urls.py`
- Test: `backend-django/reviews/tests/test_api.py`

- [ ] **Step 1: Write the failing test**

Append to `reviews/tests/test_api.py`:

```python
class PublicUserReviewsTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.pub = User.objects.create_user(
            email="pub@test.com", handle="pub", password="password123", profile_public=True
        )
        cls.priv = User.objects.create_user(
            email="priv@test.com", handle="priv", password="password123", profile_public=False
        )
        cls.book = Book.objects.create(title="B", slug="b")
        Review.objects.create(user=cls.pub, book=cls.book, body="public review")
        Review.objects.create(user=cls.priv, book=cls.book, body="private review")

    def test_public_profile_reviews_listed(self):
        resp = self.client.get("/api/u/pub/reviews/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["total"], 1)
        self.assertEqual(resp.data["data"][0]["body"], "public review")

    def test_private_profile_returns_404(self):
        resp = self.client.get("/api/u/priv/reviews/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_unknown_handle_returns_404(self):
        resp = self.client.get("/api/u/ghost/reviews/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test reviews.tests.test_api.PublicUserReviewsTest -v 2`
Expected: FAIL — 404 on `/api/u/pub/reviews/` (route not registered).

- [ ] **Step 3: Add the view**

In `reviews/views.py`, add imports:

```python
from django.http import Http404
from rest_framework import generics, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly

from users.models import User
```

Append the view at the end of the file:

```python
class UserReviewListView(generics.ListAPIView):
    """Public, paginated reviews by one user, gated by profile_public."""

    permission_classes = [AllowAny]
    serializer_class = ReviewSerializer

    def get_queryset(self):
        owner = get_object_or_404(User, handle=self.kwargs["handle"])
        if not owner.profile_public and owner != self.request.user:
            raise Http404("No User matches the given query.")
        return annotate_reviews(
            Review.objects.filter(user=owner), self.request.user
        ).order_by("-updated_at")
```

(`ReviewSerializer` is already imported in this file.)

- [ ] **Step 4: Register the route**

In `config/urls.py`, add the import and the path next to the other `api/u/<handle>/...` routes:

```python
from reviews.views import UserReviewListView
```

```python
    path("api/u/<str:handle>/reviews/", UserReviewListView.as_view()),
```

Place it right after the existing `path("api/u/<str:handle>/shelf/", ...)` line.

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test reviews.tests.test_api.PublicUserReviewsTest -v 2`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend-django/reviews/views.py backend-django/config/urls.py backend-django/reviews/tests/test_api.py
git commit -m "feat: add public user reviews endpoint"
```

---

## Task 6: Feed app + `GET /api/feed/`

**Files:**
- Create: `backend-django/feed/__init__.py`, `apps.py`, `serializers.py`, `views.py`, `urls.py`, `tests/__init__.py`, `tests/test_api.py`
- Modify: `backend-django/config/settings/` (INSTALLED_APPS), `backend-django/config/urls.py`

- [ ] **Step 1: Scaffold the app package**

```bash
cd backend-django && mkdir -p feed/tests && touch feed/__init__.py feed/tests/__init__.py
```

Create `feed/apps.py`:

```python
from django.apps import AppConfig


class FeedConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "feed"
```

- [ ] **Step 2: Register the app**

Find where local apps are listed (`grep -rn "reviews" backend-django/config/settings/`). Add `"feed",` to `INSTALLED_APPS` alongside the other local apps (e.g. after `"reviews",`).

- [ ] **Step 3: Write the failing test**

Create `feed/tests/test_api.py`:

```python
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils.timezone import now
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book
from ratings.models import Rating
from reviews.models import Review
from shelf.models import ShelfEntry
from users.models import UserFollow

User = get_user_model()
FEED_URL = "/api/feed/"


class FeedAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.me = User.objects.create_user(
            email="me@test.com", handle="me", password="password123"
        )
        cls.pub = User.objects.create_user(
            email="pub@test.com", handle="pub", password="password123", profile_public=True
        )
        cls.priv = User.objects.create_user(
            email="priv@test.com", handle="priv", password="password123", profile_public=False
        )
        cls.book = Book.objects.create(title="B", slug="b", cover_url="http://x/c.jpg")
        UserFollow.objects.create(follower=cls.me, following=cls.pub)
        UserFollow.objects.create(follower=cls.me, following=cls.priv)

    def test_requires_auth(self):
        resp = self.client.get(FEED_URL)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_feed_includes_followed_public_activity(self):
        Rating.objects.create(user=self.pub, book=self.book, rating=5)
        Review.objects.create(user=self.pub, book=self.book, body="great")
        self.client.force_authenticate(self.me)
        resp = self.client.get(FEED_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        types = {item["type"] for item in resp.data["results"]}
        self.assertEqual(types, {"rating", "review"})
        self.assertEqual(resp.data["results"][0]["actor"]["handle"], "pub")

    def test_finished_book_appears(self):
        ShelfEntry.objects.create(
            user=self.pub, book=self.book, status=ShelfEntry.Status.READ
        )
        self.client.force_authenticate(self.me)
        resp = self.client.get(FEED_URL)
        self.assertEqual(resp.data["results"][0]["type"], "finished")

    def test_private_user_excluded(self):
        Rating.objects.create(user=self.priv, book=self.book, rating=4)
        self.client.force_authenticate(self.me)
        resp = self.client.get(FEED_URL)
        self.assertEqual(resp.data["results"], [])

    def test_own_activity_excluded(self):
        Rating.objects.create(user=self.me, book=self.book, rating=3)
        self.client.force_authenticate(self.me)
        resp = self.client.get(FEED_URL)
        self.assertEqual(resp.data["results"], [])

    def test_pagination_cursor(self):
        for i in range(25):
            b = Book.objects.create(title=f"B{i}", slug=f"b{i}")
            Rating.objects.create(user=self.pub, book=b, rating=5)
        self.client.force_authenticate(self.me)
        resp = self.client.get(FEED_URL)
        self.assertEqual(len(resp.data["results"]), 20)
        self.assertIsNotNone(resp.data["next_before"])
        resp2 = self.client.get(FEED_URL, {"before": resp.data["next_before"]})
        self.assertEqual(len(resp2.data["results"]), 5)
        self.assertIsNone(resp2.data["next_before"])
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test feed.tests.test_api -v 2`
Expected: FAIL — 404 (no `/api/feed/` route).

- [ ] **Step 5: Write the serializers**

Create `feed/serializers.py`:

```python
from rest_framework import serializers


class FeedActorSerializer(serializers.Serializer):
    handle = serializers.CharField()
    display_name = serializers.CharField()
    avatar_url = serializers.CharField(allow_null=True)


class FeedBookSerializer(serializers.Serializer):
    title = serializers.CharField()
    slug = serializers.SlugField()
    cover_url = serializers.CharField(allow_null=True)


class FeedItemSerializer(serializers.Serializer):
    type = serializers.CharField()
    timestamp = serializers.DateTimeField()
    actor = FeedActorSerializer()
    book = FeedBookSerializer()
    rating = serializers.IntegerField(allow_null=True)
    body = serializers.CharField(allow_null=True)
    finish_date = serializers.DateField(allow_null=True)


class FeedResponseSerializer(serializers.Serializer):
    results = FeedItemSerializer(many=True)
    next_before = serializers.DateTimeField(allow_null=True)
```

- [ ] **Step 6: Write the view**

Create `feed/views.py`:

```python
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ratings.models import Rating
from reviews.models import Review
from shelf.models import ShelfEntry
from users.models import UserFollow

from .serializers import FeedItemSerializer, FeedResponseSerializer

PAGE_SIZE = 20
BODY_PREVIEW = 280


def _actor(user):
    return {
        "handle": user.handle,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
    }


def _book(book):
    return {"title": book.title, "slug": book.slug, "cover_url": book.cover_url}


def _rating_entry(r):
    return {
        "type": "rating",
        "timestamp": r.updated_at,
        "actor": _actor(r.user),
        "book": _book(r.book),
        "rating": r.rating,
        "body": None,
        "finish_date": None,
    }


def _review_entry(r):
    return {
        "type": "review",
        "timestamp": r.updated_at,
        "actor": _actor(r.user),
        "book": _book(r.book),
        "rating": None,
        "body": r.body[:BODY_PREVIEW],
        "finish_date": None,
    }


def _finished_entry(e):
    return {
        "type": "finished",
        "timestamp": e.updated_at,
        "actor": _actor(e.user),
        "book": _book(e.book),
        "rating": None,
        "body": None,
        "finish_date": e.finish_date,
    }


class FeedView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses=FeedResponseSerializer,
        parameters=[
            OpenApiParameter(
                name="before", type=str, required=False,
                description="ISO-8601 cursor; return activity strictly older than this.",
            )
        ],
    )
    def get(self, request):
        before_raw = request.query_params.get("before")
        before = parse_datetime(before_raw) if before_raw else now()
        if before is None:
            return Response(
                {"detail": "Invalid 'before' timestamp."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        following_ids = UserFollow.objects.filter(
            follower=request.user, following__profile_public=True
        ).values_list("following_id", flat=True)

        ratings = (
            Rating.objects.filter(user_id__in=following_ids, updated_at__lt=before)
            .select_related("user", "book")
            .order_by("-updated_at")[:PAGE_SIZE]
        )
        reviews = (
            Review.objects.filter(user_id__in=following_ids, updated_at__lt=before)
            .select_related("user", "book")
            .order_by("-updated_at")[:PAGE_SIZE]
        )
        finished = (
            ShelfEntry.objects.filter(
                user_id__in=following_ids,
                status=ShelfEntry.Status.READ,
                updated_at__lt=before,
            )
            .select_related("user", "book")
            .order_by("-updated_at")[:PAGE_SIZE]
        )

        items = (
            [_rating_entry(r) for r in ratings]
            + [_review_entry(r) for r in reviews]
            + [_finished_entry(e) for e in finished]
        )
        items.sort(key=lambda x: x["timestamp"], reverse=True)
        page = items[:PAGE_SIZE]
        next_before = (
            page[-1]["timestamp"].isoformat() if len(page) == PAGE_SIZE else None
        )

        return Response(
            {"results": FeedItemSerializer(page, many=True).data, "next_before": next_before}
        )
```

- [ ] **Step 7: Wire URLs**

Create `feed/urls.py`:

```python
from django.urls import path

from .views import FeedView

urlpatterns = [
    path("feed/", FeedView.as_view(), name="feed"),
]
```

In `config/urls.py`, add next to the other `api/` includes:

```python
    path("api/", include("feed.urls")),
```

- [ ] **Step 8: Run test to verify it passes**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test feed.tests.test_api -v 2`
Expected: PASS

- [ ] **Step 9: Lint + commit**

```bash
cd backend-django && uv run ruff check --fix . && cd ..
git add backend-django/feed/ backend-django/config/
git commit -m "feat: add on-the-fly social feed endpoint"
```

---

## Task 7: Regenerate OpenAPI + full backend suite

**Files:**
- Modify: `docs/api/openapi.yml` (regenerated)

- [ ] **Step 1: Regenerate the schema**

Run: `make regenerate-openapi`
Expected: `docs/api/openapi.yml` updated with `/api/feed/`, `/api/u/{handle}/reviews/`, `/api/reviews/{id}/like/`, and the new review fields.

- [ ] **Step 2: Run the full backend suite (incl. OpenAPI contract test)**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test`
Expected: all PASS (including `config.tests.test_openapi_schema`).

If the OpenAPI contract test fails on enum naming (e.g. `ShelfEntryStatusEnum`), check `ENUM_NAME_OVERRIDES` in settings — the M11 fix pinned that name; do not regress it.

- [ ] **Step 3: Commit**

```bash
git add docs/api/openapi.yml
git commit -m "docs: regenerate openapi for M12"
```

---

## Task 8: Frontend types + API clients

**Files:**
- Modify: `svelte-frontend/src/lib/types/review.ts`, `svelte-frontend/src/lib/api/reviews.ts`
- Create: `svelte-frontend/src/lib/types/feed.ts`, `svelte-frontend/src/lib/api/feed.ts`

- [ ] **Step 1: Extend the Review type**

In `src/lib/types/review.ts`, add to the `Review` interface:

```typescript
export interface Review {
	id: number;
	body: string;
	author: ReviewAuthor;
	author_rating: number | null;
	likes_count: number;
	is_liked: boolean;
	created_at: string;
	updated_at: string;
}
```

- [ ] **Step 2: Add feed types**

Create `src/lib/types/feed.ts`:

```typescript
export interface FeedActor {
	handle: string;
	display_name: string;
	avatar_url: string | null;
}

export interface FeedBook {
	title: string;
	slug: string;
	cover_url: string | null;
}

export interface FeedItem {
	type: 'rating' | 'review' | 'finished';
	timestamp: string;
	actor: FeedActor;
	book: FeedBook;
	rating: number | null;
	body: string | null;
	finish_date: string | null;
}

export interface FeedResponse {
	results: FeedItem[];
	next_before: string | null;
}
```

- [ ] **Step 3: Add review like + public reviews API**

In `src/lib/api/reviews.ts`, append:

```typescript
/** Like a review. Returns the updated count + flag. */
export function likeReview(fetchFn: typeof fetch, id: number) {
	return apiFetch<{ likes_count: number; is_liked: boolean }>(
		fetchFn,
		`/reviews/${id}/like/`,
		{ method: 'POST' }
	);
}

/** Unlike a review. Returns the updated count + flag. */
export function unlikeReview(fetchFn: typeof fetch, id: number) {
	return apiFetch<{ likes_count: number; is_liked: boolean }>(
		fetchFn,
		`/reviews/${id}/like/`,
		{ method: 'DELETE' }
	);
}

/** Public, paginated reviews authored by one user (newest first). */
export function fetchUserReviews(
	fetchFn: typeof fetch,
	handle: string,
	page = 1,
	isServerSide = false
) {
	return apiFetch<PaginatedResponse<Review>>(
		fetchFn,
		`/u/${encodeURIComponent(handle)}/reviews/?page=${page}`,
		undefined,
		isServerSide
	);
}
```

- [ ] **Step 4: Add feed API**

Create `src/lib/api/feed.ts`:

```typescript
import { apiFetch } from './_client';
import type { FeedResponse } from '$lib/types/feed';

/** The current user's activity feed (followed public users). */
export function fetchFeed(fetchFn: typeof fetch, before?: string, isServerSide = false) {
	const qs = before ? `?before=${encodeURIComponent(before)}` : '';
	return apiFetch<FeedResponse>(fetchFn, `/feed/${qs}`, undefined, isServerSide);
}
```

- [ ] **Step 5: Typecheck + commit**

```bash
cd svelte-frontend && npm run check && cd ..
git add svelte-frontend/src/lib/types/review.ts svelte-frontend/src/lib/types/feed.ts svelte-frontend/src/lib/api/reviews.ts svelte-frontend/src/lib/api/feed.ts
git commit -m "feat: add feed + review-like frontend API"
```

---

## Task 9: Like control on `ReviewCard`

**Files:**
- Modify: `svelte-frontend/src/lib/components/review/ReviewCard.svelte`

Check how `ReviewCard` is rendered (`grep -rn "ReviewCard" svelte-frontend/src`) and thread a `canLike` prop from the parents (`ReviewList`/`ReviewSection` on `/books/[slug]`, and the new profile section). `canLike` = user is logged in.

- [ ] **Step 1: Update `ReviewCard.svelte`**

Replace the file with:

```svelte
<script lang="ts">
	import type { Review } from '$lib/types/review';
	import RatingStars from '$lib/components/book/RatingStars.svelte';
	import { likeReview, unlikeReview } from '$lib/api/reviews';
	import { Heart } from 'lucide-svelte';

	interface Props {
		review: Review;
		canLike?: boolean;
	}
	let { review, canLike = false }: Props = $props();

	const date = $derived(new Date(review.created_at).toLocaleDateString());

	let liked = $state(review.is_liked);
	let count = $state(review.likes_count);
	let pending = $state(false);

	async function toggle() {
		if (pending) return;
		pending = true;
		const prevLiked = liked;
		const prevCount = count;
		liked = !liked;
		count += liked ? 1 : -1;
		const { data, error } = await (liked ? likeReview : unlikeReview)(fetch, review.id);
		if (error) {
			liked = prevLiked;
			count = prevCount;
		} else if (data) {
			liked = data.is_liked;
			count = data.likes_count;
		}
		pending = false;
	}
</script>

<article data-testid="review-card" class="border-b border-rule py-4">
	<div class="flex items-center justify-between gap-2">
		<a href="/u/{review.author.handle}" class="font-medium hover:text-accent transition-colors">
			{review.author.display_name || `@${review.author.handle}`}
		</a>
		{#if review.author_rating}
			<RatingStars rating={review.author_rating} readonly size="sm" />
		{/if}
	</div>
	<p class="mt-2 whitespace-pre-wrap text-sm">{review.body}</p>
	<div class="mt-1 flex items-center justify-between">
		<time class="block text-xs text-muted">{date}</time>
		{#if canLike}
			<button
				type="button"
				onclick={toggle}
				disabled={pending}
				data-testid="like-button"
				aria-pressed={liked}
				class="flex items-center gap-1 text-xs text-muted hover:text-accent transition-colors disabled:opacity-50"
			>
				<Heart size={14} class={liked ? 'fill-accent text-accent' : ''} />
				<span data-testid="like-count">{count}</span>
			</button>
		{:else}
			<span class="flex items-center gap-1 text-xs text-muted">
				<Heart size={14} />
				<span data-testid="like-count">{count}</span>
			</span>
		{/if}
	</div>
</article>
```

- [ ] **Step 2: Thread `canLike` from `/books/[slug]` review rendering**

Open the component that renders `ReviewCard` on the book page (`ReviewList.svelte` / `ReviewSection.svelte`). Add a `canLike` prop to it and pass it down to each `<ReviewCard {review} {canLike} />`. Source `canLike` from the existing logged-in signal on `/books/[slug]` (the same one gating the review form). If the book page already passes an `isLoggedIn`/`user` value into the review section, reuse it; otherwise add the prop along the existing chain.

- [ ] **Step 3: Typecheck + lint**

Run: `cd svelte-frontend && npm run check && npm run lint`
Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/src/lib/components/review/
git commit -m "feat: add like control to ReviewCard"
```

---

## Task 10: `/feed` route

**Files:**
- Create: `svelte-frontend/src/routes/feed/+page.server.ts`, `+page.svelte`, `svelte-frontend/src/lib/components/feed/FeedItem.svelte`

- [ ] **Step 1: Server loader (auth-gated)**

Create `src/routes/feed/+page.server.ts`:

```typescript
import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { fetchFeed } from '$lib/api/feed';

export const load: PageServerLoad = async ({ fetch, parent }) => {
	const { user } = await parent();
	if (!user) {
		throw redirect(302, '/login');
	}
	const { data } = await fetchFeed(fetch, undefined, true);
	return {
		items: data?.results ?? [],
		nextBefore: data?.next_before ?? null
	};
};
```

(If `parent()` does not expose `user`, mirror the auth-gating used by `/shelf` or `/stats` `+page.server.ts`.)

- [ ] **Step 2: FeedItem component**

Create `src/lib/components/feed/FeedItem.svelte`:

```svelte
<script lang="ts">
	import type { FeedItem } from '$lib/types/feed';
	import Avatar from '$lib/components/Avatar.svelte';

	interface Props {
		item: FeedItem;
	}
	let { item }: Props = $props();

	const date = $derived(new Date(item.timestamp).toLocaleDateString());
	const name = $derived(item.actor.display_name || `@${item.actor.handle}`);
	const verb = $derived(
		item.type === 'rating'
			? `rated ${item.rating}/5`
			: item.type === 'review'
				? 'reviewed'
				: 'finished'
	);
</script>

<article data-testid="feed-item" class="flex gap-3 border-b border-rule py-4">
	<Avatar src={item.actor.avatar_url} name={name} size="sm" />
	<div class="min-w-0 flex-1">
		<p class="text-sm">
			<a href="/u/{item.actor.handle}" class="font-medium hover:text-accent transition-colors"
				>{name}</a
			>
			<span class="text-muted">{verb}</span>
			<a href="/books/{item.book.slug}" class="font-medium hover:text-accent transition-colors"
				>{item.book.title}</a
			>
		</p>
		{#if item.type === 'review' && item.body}
			<p class="mt-1 whitespace-pre-wrap text-sm text-muted">{item.body}</p>
		{/if}
		<time class="mt-1 block text-xs text-muted">{date}</time>
	</div>
</article>
```

(Check `Avatar.svelte`'s actual props with `grep "Props\|\\$props" svelte-frontend/src/lib/components/Avatar.svelte` and adjust `src`/`name`/`size` to match its real signature.)

- [ ] **Step 3: Feed page with Load more**

Create `src/routes/feed/+page.svelte`:

```svelte
<script lang="ts">
	import type { PageProps } from './$types';
	import FeedItem from '$lib/components/feed/FeedItem.svelte';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import { Button } from '$lib/components/ui/button';
	import { fetchFeed } from '$lib/api/feed';
	import type { FeedItem as FeedItemType } from '$lib/types/feed';

	let { data }: PageProps = $props();

	let items = $state<FeedItemType[]>(data.items);
	let nextBefore = $state<string | null>(data.nextBefore);
	let loading = $state(false);

	async function loadMore() {
		if (!nextBefore || loading) return;
		loading = true;
		const { data: page } = await fetchFeed(fetch, nextBefore);
		if (page) {
			items = [...items, ...page.results];
			nextBefore = page.next_before;
		}
		loading = false;
	}
</script>

<section class="mx-auto max-w-2xl px-4 py-8">
	<h1 class="font-display text-2xl font-semibold text-ink mb-6">Feed</h1>
	{#if items.length === 0}
		<EmptyState message="Follow some people to see their activity here." />
	{:else}
		{#each items as item (item.type + item.timestamp + item.book.slug)}
			<FeedItem {item} />
		{/each}
		{#if nextBefore}
			<div class="mt-6 text-center">
				<Button variant="ghost" onclick={loadMore} disabled={loading}>
					{loading ? 'Loading…' : 'Load more'}
				</Button>
			</div>
		{/if}
	{/if}
</section>
```

(Confirm `EmptyState.svelte`'s prop name — `grep "Props\|\\$props" svelte-frontend/src/lib/components/EmptyState.svelte` — and adjust `message` if it differs.)

- [ ] **Step 4: Typecheck + lint**

Run: `cd svelte-frontend && npm run check && npm run lint`
Expected: no errors.

- [ ] **Step 5: Commit**

```bash
git add svelte-frontend/src/routes/feed/ svelte-frontend/src/lib/components/feed/
git commit -m "feat: add /feed page"
```

---

## Task 11: Reviews section on profile

**Files:**
- Modify: `svelte-frontend/src/routes/u/[handle]/+page.server.ts`, `+page.svelte`

- [ ] **Step 1: Load user reviews in the profile loader**

In `src/routes/u/[handle]/+page.server.ts`, add the import and fetch, then return it:

```typescript
import { fetchUserReviews } from '$lib/api/reviews';
```

After the existing `fetchPublicShelf` call:

```typescript
	const { data: reviews } = await fetchUserReviews(fetch, params.handle, 1, true);
```

Extend the returned object:

```typescript
	return {
		profile,
		isOwner,
		isLoggedIn,
		shelves: shelves ?? [],
		reading: reading ?? [],
		reviews: reviews?.data ?? []
	};
```

- [ ] **Step 2: Render the Reviews section**

In `src/routes/u/[handle]/+page.svelte`:

Add imports in `<script>`:

```typescript
	import ReviewCard from '$lib/components/review/ReviewCard.svelte';
	import type { Review } from '$lib/types/review';
```

Add a derived value next to the existing ones:

```typescript
	let reviews: Review[] = $derived(data.reviews);
```

Add the section after the existing `Reading` section (`{#if reading.length > 0} ... {/if}`):

```svelte
	{#if reviews.length > 0}
		<section class="mt-10">
			<h2 class="font-display text-xl font-medium text-ink mb-4">Reviews</h2>
			{#each reviews as review (review.id)}
				<ReviewCard {review} canLike={data.isLoggedIn} />
			{/each}
		</section>
	{/if}
```

(YAGNI: no Load more on the profile reviews section for M12 — first page only. If the profile already has a pattern for paginated sections, this can be added later.)

- [ ] **Step 3: Typecheck + lint**

Run: `cd svelte-frontend && npm run check && npm run lint`
Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/src/routes/u/
git commit -m "feat: add reviews section to profile"
```

---

## Task 12: Feed nav link

**Files:**
- Modify: `svelte-frontend/src/lib/components/shell/AppShell.svelte`

- [ ] **Step 1: Add the link**

In `AppShell.svelte`, inside the `{#if user}` block of the nav (next to Shelf/Stats):

```svelte
				{#if user}
					<Button variant="ghost" size="sm" href={resolve('/feed')}>Feed</Button>
					<Button variant="ghost" size="sm" href={resolve('/shelf')}>Shelf</Button>
					<Button variant="ghost" size="sm" href={resolve('/stats')}>Stats</Button>
				{/if}
```

- [ ] **Step 2: Typecheck + commit**

```bash
cd svelte-frontend && npm run check && cd ..
git add svelte-frontend/src/lib/components/shell/AppShell.svelte
git commit -m "feat: add Feed nav link"
```

---

## Task 13: E2E coverage

**Files:**
- Create: `svelte-frontend/e2e/tests/social-feed.spec.ts` (adjust path to match the existing E2E test dir — `ls svelte-frontend/e2e` / wherever `*.spec.ts` live)

Inspect an existing spec (e.g. `stats.spec.ts` or the follow spec) for the seeding/login helpers used in `global-setup.ts`, then mirror them.

- [ ] **Step 1: Write the E2E spec**

Create the spec following existing conventions. Cover three flows:

```typescript
import { test, expect } from '@playwright/test';
// import shared login/seed helpers the same way other specs do

test.describe('M12 social feed', () => {
	test('feed shows followed user activity', async ({ page }) => {
		// log in as a user who follows someone with public activity (seed in global-setup or inline via API)
		await page.goto('/feed');
		await expect(page.getByTestId('feed-item').first()).toBeVisible();
	});

	test('can like a review', async ({ page }) => {
		// navigate to a book page or profile with a review
		const likeBtn = page.getByTestId('like-button').first();
		const count = page.getByTestId('like-count').first();
		const before = Number(await count.innerText());
		await likeBtn.click();
		await expect(count).toHaveText(String(before + 1));
	});

	test('profile shows reviews section', async ({ page }) => {
		// go to a public profile that has at least one review
		await page.goto('/u/<seeded-public-handle>');
		await expect(page.getByRole('heading', { name: 'Reviews' })).toBeVisible();
		await expect(page.getByTestId('review-card').first()).toBeVisible();
	});
});
```

Replace `<seeded-public-handle>` and the login/seed steps with the project's actual helpers. If seeded data does not cover a followed-user-with-activity case, extend `global-setup.ts` to create it via API (the established seeding approach).

- [ ] **Step 2: Run E2E**

Run: `cd svelte-frontend && npx playwright test social-feed`
Expected: all three PASS. (If the register/login throttle blocks the run, restart the django container — known E2E gotcha — and re-run.)

- [ ] **Step 3: Commit**

```bash
git add svelte-frontend/e2e/
git commit -m "test: e2e for social feed, likes, profile reviews"
```

---

## Task 14: Final verification

- [ ] **Step 1: Full backend suite**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test`
Expected: all PASS.

- [ ] **Step 2: Frontend checks**

Run: `cd svelte-frontend && npm run check && npm run lint`
Expected: no errors.

- [ ] **Step 3: Lint backend**

Run: `cd backend-django && uv run ruff check .`
Expected: clean.

- [ ] **Step 4: Update docs**

Update `docs/ARCHITECTURE.md` API surface to list `/api/feed/`, `/api/u/{handle}/reviews/`, `/api/reviews/{id}/like/`, and add `feed/` to the Django apps table. Move M12 from "W toku" to "Zrobione" in `docs/ROADMAP.md` only when the branch is merged (per `/finishing-a-development-branch`).

```bash
git add docs/ARCHITECTURE.md
git commit -m "docs: document M12 endpoints"
```

Then proceed to `/requesting-code-review` and `/finishing-a-development-branch`.

---

## Self-Review notes

- **Spec coverage:** Feed (Task 6), `ReviewLike` model+endpoint (Tasks 2–3), `likes_count`/`is_liked` (Task 4), public reviews (Task 5), `ShelfEntry.updated_at` (Task 1), `/feed` page (Task 10), profile reviews section (Task 11), like control on `ReviewCard` (Task 9), nav link (Task 12), OpenAPI regen (Task 7), tests (each task + Task 13). All spec sections mapped.
- **Naming consistency:** `annotate_reviews(qs, user)` used in Tasks 4 & 5; `likes_count`/`is_liked` field names consistent across model annotations, serializer, types, and `like` action response; `next_before` cursor consistent across feed view, serializer, API client, and page.
- **YAGNI:** no `Activity` model, no notifications/comments/reposts, no like on feed items, no Load more on profile reviews.
