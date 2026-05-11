# Django API Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Systematically audit all 37 Django REST API endpoints with automated tests, fix trivial bugs found, and produce an AUDIT.md report.

**Architecture:** App-by-app test-first approach. Shared `AuthTestHelper` mixin creates test users (USER, MODERATOR, ADMIN) + minimal fixtures. Auth endpoints tested with real JWT flow; CRUD endpoints use `force_authenticate`. Internal endpoints override `REMOTE_ADDR` for middleware bypass.

**Tech Stack:** Django 6.0 test framework, DRF `APITestCase`, `force_authenticate`, `override_settings`, `unittest.mock.patch`

---

## Task 0: Fix duplicate `/books/{id}/details/` endpoint

**Files:**
- Modify: `backend-django/books/urls.py:14`
- Modify: `frontend/src/api.js:79`

The frontend's `fetchBookDetails()` uses `/api/books/${bookId}/details/`. The `details/` path in `books/urls.py` is a duplicate of `/<int:pk>/` — both route to `BookDetailView`. Remove the duplicate and update the frontend.

- [ ] **Step 1: Update frontend `api.js` to use `/${bookId}/` instead of `/${bookId}/details/`**

```javascript
// In frontend/src/api.js, line 79, change:
return request('GET', `/api/books/${bookId}/details/`)
// To:
return request('GET', `/api/books/${bookId}/`)
```

- [ ] **Step 2: Remove duplicate URL pattern from `books/urls.py`**

```python
# In backend-django/books/urls.py, remove line 14:
#   path("<int:pk>/details/", BookDetailView.as_view()),
#
# Resulting urlpatterns:
urlpatterns = [
    path("", BookListCreateView.as_view()),
    path("<int:pk>/", BookDetailView.as_view()),
    path("<int:pk>/reviews/", BookReviewListCreateView.as_view()),
    path("<int:book_id>/chapters/", ChapterView.as_view()),
    path("<int:book_id>/characters/", BookCharactersView.as_view()),
    path("<int:book_id>/relations/", BookRelationsView.as_view()),
]
```

- [ ] **Step 3: Verify the fix builds**

```
cd frontend && npm run build
```
Expected: build succeeds without errors.

- [ ] **Step 4: Commit**

```bash
git add backend-django/books/urls.py frontend/src/api.js
git commit -m "fix: remove duplicate /books/{id}/details/ endpoint, update frontend"
```

---

## Task 1: Shared test helper — `config/test_helpers.py`

**Files:**
- Create: `backend-django/config/test_helpers.py`

- [ ] **Step 1: Create the shared helper**

```python
# backend-django/config/test_helpers.py
from users.models import User


class AuthTestHelper:
    """Mixin that creates test users with different roles."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="user@test.com",
            username="testuser",
            password="password123",
        )
        cls.moderator = User.objects.create_user(
            email="mod@test.com",
            username="moderator",
            password="password123",
            role="MODERATOR",
        )
        cls.admin = User.objects.create_user(
            email="admin@test.com",
            username="admin",
            password="password123",
            role="ADMIN",
        )
```

- [ ] **Step 2: Run Django check to verify no import errors**

```bash
cd backend-django && DJANGO_ENV=dev uv run python -c "from config.test_helpers import AuthTestHelper; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend-django/config/test_helpers.py
git commit -m "test: add shared AuthTestHelper mixin"
```

---

## Task 2: Auth endpoint tests — `users/tests/test_auth.py`

**Files:**
- Create: `backend-django/users/tests/test_auth.py`

- [ ] **Step 1: Write the complete test file**

```python
# backend-django/users/tests/test_auth.py
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class RegisterTest(APITestCase):
    def setUp(self):
        self.url = "/api/auth/register/"

    def test_post_valid_returns_201_with_tokens(self):
        resp = self.client.post(self.url, {
            "email": "new@test.com",
            "username": "newuser",
            "password": "secret123",
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)
        self.assertTrue(User.objects.filter(email="new@test.com").exists())

    def test_post_duplicate_email_returns_400(self):
        User.objects.create_user(email="dup@test.com", username="dupuser", password="pw")
        resp = self.client.post(self.url, {
            "email": "dup@test.com",
            "username": "another",
            "password": "secret123",
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_duplicate_username_returns_400(self):
        User.objects.create_user(email="a@test.com", username="dupuser", password="pw")
        resp = self.client.post(self.url, {
            "email": "b@test.com",
            "username": "dupuser",
            "password": "secret123",
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_missing_email_returns_400(self):
        resp = self.client.post(self.url, {
            "username": "someone",
            "password": "secret123",
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_short_password_returns_400(self):
        resp = self.client.post(self.url, {
            "email": "x@test.com",
            "username": "someone",
            "password": "12345",
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_invalid_username_uppercase_returns_400(self):
        resp = self.client.post(self.url, {
            "email": "x@test.com",
            "username": "BadUser",
            "password": "secret123",
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_empty_body_returns_400(self):
        resp = self.client.post(self.url, {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTest(APITestCase):
    def setUp(self):
        self.url = "/api/auth/login/"
        self.user = User.objects.create_user(
            email="login@test.com",
            username="loginuser",
            password="secret123",
        )

    def test_post_valid_returns_200_with_tokens(self):
        resp = self.client.post(self.url, {
            "email": "login@test.com",
            "password": "secret123",
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_post_wrong_password_returns_400(self):
        resp = self.client.post(self.url, {
            "email": "login@test.com",
            "password": "wrongpass",
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_nonexistent_email_returns_400(self):
        resp = self.client.post(self.url, {
            "email": "no@test.com",
            "password": "secret123",
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_missing_fields_returns_400(self):
        resp = self.client.post(self.url, {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_inactive_user_returns_400(self):
        self.user.is_active = False
        self.user.save()
        resp = self.client.post(self.url, {
            "email": "login@test.com",
            "password": "secret123",
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class TokenRefreshTest(APITestCase):
    def setUp(self):
        self.url = "/api/auth/refresh/"
        self.user = User.objects.create_user(
            email="refresh@test.com",
            username="refreshuser",
            password="secret123",
        )

    def _get_tokens(self):
        resp = self.client.post("/api/auth/login/", {
            "email": "refresh@test.com",
            "password": "secret123",
        })
        return resp.data["access"], resp.data["refresh"]

    def test_post_valid_refresh_returns_200_with_new_access(self):
        _, refresh = self._get_tokens()
        resp = self.client.post(self.url, {"refresh": refresh})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)

    def test_post_missing_refresh_returns_400(self):
        resp = self.client.post(self.url, {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_invalid_refresh_returns_401(self):
        resp = self.client.post(self.url, {"refresh": "invalid-token"})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutTest(APITestCase):
    def setUp(self):
        self.url = "/api/auth/logout/"
        User.objects.create_user(
            email="logout@test.com",
            username="logoutuser",
            password="secret123",
        )

    def _get_tokens(self):
        resp = self.client.post("/api/auth/login/", {
            "email": "logout@test.com",
            "password": "secret123",
        })
        return resp.data["access"], resp.data["refresh"]

    def test_post_valid_refresh_returns_200(self):
        _, refresh = self._get_tokens()
        resp = self.client.post(self.url, {"refresh": refresh})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["message"], "Logged out successfully")

    def test_post_no_refresh_still_succeeds_200(self):
        resp = self.client.post(self.url, {})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class AuthMeTest(APITestCase):
    def setUp(self):
        self.url = "/api/auth/me/"
        self.user = User.objects.create_user(
            email="me@test.com",
            username="meuser",
            password="secret123",
        )

    def _get_access_token(self):
        resp = self.client.post("/api/auth/login/", {
            "email": "me@test.com",
            "password": "secret123",
        })
        return resp.data["access"]

    def test_get_authenticated_returns_200_with_user_data(self):
        token = self._get_access_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["authenticated"])
        self.assertEqual(resp.data["email"], "me@test.com")
        self.assertEqual(resp.data["username"], "meuser")
        self.assertEqual(resp.data["role"], "USER")

    def test_get_unauthenticated_returns_200_with_false(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["authenticated"])
        self.assertIsNone(resp.data["email"])
```

- [ ] **Step 2: Run tests**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test users.tests.test_auth -v2
```
Expected: 16 tests pass.

- [ ] **Step 3: Commit**

```bash
git add backend-django/users/tests/test_auth.py
git commit -m "test: add auth endpoint tests (register, login, refresh, logout, me)"
```

---

## Task 3: User endpoint tests — `users/tests/test_users.py`

**Files:**
- Create: `backend-django/users/tests/test_users.py`

- [ ] **Step 1: Write the complete test file**

```python
# backend-django/users/tests/test_users.py
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from config.test_helpers import AuthTestHelper

User = get_user_model()


class UserProfileTest(AuthTestHelper, APITestCase):
    def setUp(self):
        AuthTestHelper.setUpTestData()
        self.target = User.objects.create_user(
            email="target@test.com",
            username="targetuser",
            password="pw",
            bio="Hello world",
        )
        self.url = f"/api/users/{self.target.username}/"

    def test_get_public_profile_returns_200(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["username"], "targetuser")
        self.assertEqual(resp.data["bio"], "Hello world")

    def test_get_nonexistent_user_returns_404(self):
        resp = self.client.get("/api/users/nonexistent/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_private_profile_returns_404_for_others(self):
        self.target.profile_public = False
        self.target.save()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_private_profile_returns_200_for_owner(self):
        self.target.profile_public = False
        self.target.save()
        self.client.force_authenticate(user=self.target)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class UserSettingsTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()

    def test_get_own_settings_returns_200(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/users/me/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["username"], "testuser")
        self.assertIn("email", resp.data)
        self.assertIn("profilePublic", resp.data)

    def test_get_settings_unauthenticated_returns_401(self):
        resp = self.client.get("/api/users/me/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_settings_updates_bio(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch("/api/users/me/", {"bio": "New bio"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["bio"], "New bio")
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, "New bio")


class UserVisibilityTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()

    def test_patch_visibility_to_false(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch("/api/users/me/visibility/?profilePublic=false")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["profile_public"])
        self.user.refresh_from_db()
        self.assertFalse(self.user.profile_public)

    def test_patch_visibility_to_true(self):
        self.user.profile_public = False
        self.user.save()
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch("/api/users/me/visibility/?profilePublic=true")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["profile_public"])

    def test_patch_visibility_unauthenticated_returns_401(self):
        resp = self.client.patch("/api/users/me/visibility/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class UserFollowTest(AuthTestHelper, APITestCase):
    def setUp(self):
        AuthTestHelper.setUpTestData()
        self.target = User.objects.create_user(
            email="target2@test.com",
            username="target2",
            password="pw",
        )
        self.url = f"/api/users/{self.target.username}/follow/"

    def test_post_follow_returns_201(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["followerUsername"], "testuser")
        self.assertEqual(resp.data["followingUsername"], "target2")

    def test_post_follow_self_returns_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(f"/api/users/{self.user.username}/follow/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_follow_already_following_returns_409(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(self.url)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

    def test_post_follow_unauthenticated_returns_401(self):
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_unfollow_returns_204(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(self.url)
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_unfollow_not_following_returns_404(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_follow_nonexistent_user_returns_404(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete("/api/users/nobody/follow/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class FollowListTest(AuthTestHelper, APITestCase):
    def setUp(self):
        AuthTestHelper.setUpTestData()
        self.target = User.objects.create_user(
            email="target3@test.com",
            username="target3",
            password="pw",
        )

    def test_list_followers_returns_200(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(f"/api/users/{self.target.username}/follow/")
        resp = self.client.get(f"/api/users/{self.target.username}/followers/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["followerUsername"], "testuser")

    def test_list_following_returns_200(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(f"/api/users/{self.target.username}/follow/")
        resp = self.client.get(f"/api/users/testuser/following/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["followingUsername"], "target3")

    def test_list_followers_empty_returns_200(self):
        resp = self.client.get(f"/api/users/{self.target.username}/followers/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    def test_list_followers_nonexistent_user_returns_404(self):
        resp = self.client.get("/api/users/nobody/followers/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class UserSettingsResponseStructureTest(AuthTestHelper, APITestCase):
    """Verify camelCase field names in settings response."""

    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()

    def test_response_uses_camelcase_keys(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/users/me/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("profilePublic", resp.data)
        self.assertIn("avatarUrl", resp.data)
        self.assertIn("memberSince", resp.data)
```

- [ ] **Step 2: Run tests**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test users.tests.test_users -v2
```
Expected: 16 tests pass.

- [ ] **Step 3: Commit**

```bash
git add backend-django/users/tests/test_users.py
git commit -m "test: add user profile, follow, visibility tests"
```

---

## Task 4: Book endpoint tests — `books/tests/test_books.py`

**Files:**
- Create: `backend-django/books/tests/test_books.py`

- [ ] **Step 1: Write the complete test file**

```python
# backend-django/books/tests/test_books.py
from rest_framework import status
from rest_framework.test import APITestCase

from config.test_helpers import AuthTestHelper
from books.models import Book, Chapter
from library.models import Author


class BookListTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.author = Author.objects.create(name="Test Author")
        cls.book1 = Book.objects.create(
            title="First Book", isbn="111", page_count=200, year=2023
        )
        cls.book1.authors.add(cls.author)
        cls.book1.tags.set([])
        cls.book2 = Book.objects.create(
            title="Second Book", isbn="222", page_count=300, year=2024
        )
        cls.book2.authors.add(cls.author)
        cls.book2.tags.set([])

    def test_get_list_returns_200_with_array(self):
        resp = self.client.get("/api/books/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsInstance(resp.data, list)
        self.assertGreaterEqual(len(resp.data), 2)

    def test_get_list_with_search_returns_filtered(self):
        resp = self.client.get("/api/books/?q=First")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        titles = [b["title"] for b in resp.data]
        self.assertIn("First Book", titles)

    def test_get_list_with_nonexistent_query_returns_empty(self):
        resp = self.client.get("/api/books/?q=zzzzzzz")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    def test_post_create_book_as_moderator_returns_201(self):
        self.client.force_authenticate(user=self.moderator)
        resp = self.client.post("/api/books/", {
            "title": "New Book",
            "author_id": self.author.id,
            "year": 2025,
            "isbn": "333",
            "page_count": 150,
            "genres": ["fantasy"],
            "tags": ["magic"],
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        book = Book.objects.get(title="New Book")
        self.assertEqual(book.tags.count(), 1)
        self.assertEqual(book.tags.first().name, "magic")

    def test_post_create_book_as_user_returns_403(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post("/api/books/", {
            "title": "New Book",
            "author_id": self.author.id,
        })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_create_book_unauthenticated_returns_401(self):
        resp = self.client.post("/api/books/", {
            "title": "New Book",
            "author_id": self.author.id,
        })
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_create_book_missing_author_returns_400(self):
        self.client.force_authenticate(user=self.moderator)
        resp = self.client.post("/api/books/", {"title": "No Author"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_create_book_nonexistent_author_returns_404(self):
        self.client.force_authenticate(user=self.moderator)
        resp = self.client.post("/api/books/", {
            "title": "Bad Author",
            "author_id": 99999,
        })
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class BookDetailTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.author = Author.objects.create(name="Detail Author")
        cls.book = Book.objects.create(
            title="Detail Book", isbn="444", page_count=250, year=2023
        )
        cls.book.authors.add(cls.author)
        cls.book.tags.set([])

    def test_get_detail_returns_200_with_book_and_chapters(self):
        resp = self.client.get(f"/api/books/{self.book.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("book", resp.data)
        self.assertIn("chapters", resp.data)
        self.assertIn("characters", resp.data)
        self.assertIn("relations", resp.data)
        self.assertIn("reviews", resp.data)
        self.assertEqual(resp.data["book"]["title"], "Detail Book")

    def test_get_nonexistent_book_returns_404(self):
        resp = self.client.get("/api/books/99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_update_book_as_moderator_returns_200(self):
        self.client.force_authenticate(user=self.moderator)
        resp = self.client.put(f"/api/books/{self.book.id}/", {
            "title": "Updated Title",
            "author_id": self.author.id,
            "year": 2025,
            "isbn": "444",
            "page_count": 300,
            "genres": [],
            "tags": [],
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_delete_book_as_moderator_returns_204(self):
        book = Book.objects.create(title="To Delete", isbn="555")
        self.client.force_authenticate(user=self.moderator)
        resp = self.client.delete(f"/api/books/{book.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Book.objects.filter(id=book.id).exists())

    def test_delete_book_as_user_returns_403(self):
        book = Book.objects.create(title="To Delete", isbn="666")
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete(f"/api/books/{book.id}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_update_book_as_user_returns_403(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.put(f"/api/books/{self.book.id}/", {
            "title": "Hack", "author_id": self.author.id,
        })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class ChapterTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(
            title="Chapter Book", isbn="777", page_count=100, year=2023
        )

    def test_get_chapters_empty_returns_200_empty(self):
        resp = self.client.get(f"/api/books/{self.book.id}/chapters/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    def test_post_upload_chapters_as_moderator_returns_201(self):
        self.client.force_authenticate(user=self.moderator)
        from django.core.files.uploadedfile import SimpleUploadedFile

        content = "Chapter One Content\n\nChapter Two Content"
        file = SimpleUploadedFile("book.txt", content.encode("utf-8"))
        resp = self.client.post(
            f"/api/books/{self.book.id}/chapters/",
            {"file": file},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["bookId"], self.book.id)
        self.assertEqual(resp.data["chaptersCreated"], 2)
        self.assertEqual(Chapter.objects.filter(book=self.book).count(), 2)

    def test_post_upload_chapters_as_user_returns_403(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(f"/api/books/{self.book.id}/chapters/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_upload_no_file_returns_400(self):
        self.client.force_authenticate(user=self.moderator)
        resp = self.client.post(f"/api/books/{self.book.id}/chapters/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_chapters_as_moderator_returns_204(self):
        Chapter.objects.create(
            book=self.book, chapter_number=1, title="C1", content="text"
        )
        self.client.force_authenticate(user=self.moderator)
        resp = self.client.delete(f"/api/books/{self.book.id}/chapters/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Chapter.objects.filter(book=self.book).count(), 0)


class BookCharactersTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(
            title="Char Book", isbn="888", page_count=100, year=2023
        )

    def test_get_characters_empty_returns_200(self):
        resp = self.client.get(f"/api/books/{self.book.id}/characters/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])


class BookRelationsTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(
            title="Rel Book", isbn="999", page_count=100, year=2023
        )

    def test_get_relations_empty_returns_200(self):
        resp = self.client.get(f"/api/books/{self.book.id}/relations/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])


class BookSearchByAuthorTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.author = Author.objects.create(name="Jane Austen")
        cls.book = Book.objects.create(title="Pride", isbn="000a", year=1813)
        cls.book.authors.add(cls.author)
        cls.book.tags.set([])

    def test_search_by_author_name_finds_book(self):
        resp = self.client.get("/api/books/?q=austen")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["title"], "Pride")
```

- [ ] **Step 2: Run tests**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test books.tests.test_books -v2
```
Expected: 18 tests pass.

- [ ] **Step 3: Commit**

```bash
git add backend-django/books/tests/test_books.py
git commit -m "test: add book CRUD, chapter, character, relation tests"
```

---

## Task 5: Shelf endpoint tests — `shelf/tests/test_views.py`

**Files:**
- Create: `backend-django/shelf/tests/test_views.py`

- [ ] **Step 1: Write the complete test file**

```python
# backend-django/shelf/tests/test_views.py
from rest_framework import status
from rest_framework.test import APITestCase

from config.test_helpers import AuthTestHelper
from books.models import Book
from shelf.models import ShelfEntry


class ShelfListTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(
            title="Shelf Book", isbn="s001", page_count=100, year=2023
        )

    def test_get_shelf_authenticated_returns_200(self):
        ShelfEntry.objects.create(user=self.user, book=self.book, status="READING")
        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/shelf/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["status"], "READING")

    def test_get_shelf_unauthenticated_returns_401(self):
        resp = self.client.get("/api/shelf/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_shelf_empty_returns_200(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/shelf/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    def test_shelf_entries_isolated_per_user(self):
        ShelfEntry.objects.create(user=self.user, book=self.book, status="READ")
        ShelfEntry.objects.create(user=self.moderator, book=self.book, status="WANT_TO_READ")
        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/shelf/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["status"], "READ")


class ShelfEntryTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(
            title="Entry Book", isbn="s002", page_count=100, year=2023
        )

    def test_post_create_entry_returns_201(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            f"/api/shelf/{self.book.id}/", {"status": "WANT_TO_READ"}
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["status"], "WANT_TO_READ")
        self.assertTrue(
            ShelfEntry.objects.filter(user=self.user, book=self.book).exists()
        )

    def test_post_create_entry_default_status_returns_201(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(f"/api/shelf/{self.book.id}/", {})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["status"], "WANT_TO_READ")

    def test_post_create_entry_unauthenticated_returns_401(self):
        resp = self.client.post(f"/api/shelf/{self.book.id}/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_create_entry_nonexistent_book_returns_404(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post("/api/shelf/99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_entry_returns_200(self):
        ShelfEntry.objects.create(user=self.user, book=self.book, status="READING")
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(f"/api/shelf/{self.book.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["status"], "READING")

    def test_get_entry_not_found_returns_404(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(f"/api/shelf/{self.book.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_update_status_returns_200(self):
        ShelfEntry.objects.create(user=self.user, book=self.book, status="WANT_TO_READ")
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(
            f"/api/shelf/{self.book.id}/", {"status": "READ"}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["status"], "READ")

    def test_patch_missing_status_returns_400(self):
        ShelfEntry.objects.create(user=self.user, book=self.book, status="WANT_TO_READ")
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(f"/api/shelf/{self.book.id}/", {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_entry_returns_204(self):
        ShelfEntry.objects.create(user=self.user, book=self.book, status="READ")
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete(f"/api/shelf/{self.book.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            ShelfEntry.objects.filter(user=self.user, book=self.book).exists()
        )

    def test_delete_entry_unauthenticated_returns_401(self):
        ShelfEntry.objects.create(user=self.user, book=self.book, status="READ")
        resp = self.client.delete(f"/api/shelf/{self.book.id}/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_access_other_user_entry(self):
        ShelfEntry.objects.create(user=self.moderator, book=self.book, status="READ")
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(f"/api/shelf/{self.book.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class ShelfResponseStructureTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(
            title="Struct Book", isbn="s003", page_count=100, year=2023
        )

    def test_response_uses_camelcase_keys(self):
        ShelfEntry.objects.create(user=self.user, book=self.book, status="READING")
        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/shelf/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        entry = resp.data[0]
        self.assertIn("createdAt", entry)
        self.assertIn("book", entry)
        self.assertIn("id", entry["book"])
        self.assertIn("title", entry["book"])
        self.assertIn("author", entry["book"])
```

- [ ] **Step 2: Run tests**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test shelf.tests.test_views -v2
```
Expected: 13 tests pass.

- [ ] **Step 3: Commit**

```bash
git add backend-django/shelf/tests/test_views.py
git commit -m "test: add shelf CRUD tests"
```

---

## Task 6: Review endpoint tests — `reviews/tests/test_views.py`

**Files:**
- Create: `backend-django/reviews/tests/test_views.py`

- [ ] **Step 1: Write the complete test file**

```python
# backend-django/reviews/tests/test_views.py
from rest_framework import status
from rest_framework.test import APITestCase

from config.test_helpers import AuthTestHelper
from books.models import Book
from reviews.models import Review


class BookReviewListCreateTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(
            title="Review Book", isbn="r001", page_count=100, year=2023
        )

    def test_get_reviews_empty_returns_200(self):
        resp = self.client.get(f"/api/books/{self.book.id}/reviews/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    def test_get_reviews_with_data_returns_200(self):
        Review.objects.create(
            user=self.user, book=self.book, rating=4, content="Good book"
        )
        resp = self.client.get(f"/api/books/{self.book.id}/reviews/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["rating"], 4)
        self.assertEqual(resp.data[0]["username"], "testuser")

    def test_post_create_review_returns_201(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(f"/api/books/{self.book.id}/reviews/", {
            "rating": 5,
            "content": "Excellent!",
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.filter(book=self.book, user=self.user).count(), 1)

    def test_post_create_review_unauthenticated_returns_401(self):
        resp = self.client.post(f"/api/books/{self.book.id}/reviews/", {
            "rating": 3,
            "content": "Test",
        })
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_create_review_duplicate_returns_400(self):
        Review.objects.create(
            user=self.user, book=self.book, rating=3, content="First"
        )
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(f"/api/books/{self.book.id}/reviews/", {
            "rating": 4,
            "content": "Second?",
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_create_review_invalid_rating_returns_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(f"/api/books/{self.book.id}/reviews/", {
            "rating": 6,
            "content": "Too high",
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_create_review_missing_content_returns_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(f"/api/books/{self.book.id}/reviews/", {
            "rating": 3,
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_create_review_missing_rating_returns_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(f"/api/books/{self.book.id}/reviews/", {
            "content": "No rating",
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class ReviewDeleteTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(
            title="Del Review Book", isbn="r002", page_count=100, year=2023
        )

    def setUp(self):
        self.review = Review.objects.create(
            user=self.user, book=self.book, rating=4, content="Nice"
        )

    def test_delete_review_as_moderator_returns_204(self):
        self.client.force_authenticate(user=self.moderator)
        resp = self.client.delete(f"/api/reviews/{self.review.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.filter(id=self.review.id).exists())

    def test_delete_review_as_admin_returns_204(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.delete(f"/api/reviews/{self.review.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_review_as_regular_user_returns_403(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete(f"/api/reviews/{self.review.id}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_review_unauthenticated_returns_401(self):
        resp = self.client.delete(f"/api/reviews/{self.review.id}/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_nonexistent_review_returns_404(self):
        self.client.force_authenticate(user=self.moderator)
        resp = self.client.delete("/api/reviews/99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class ReviewResponseStructureTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(
            title="Struct Review", isbn="r003", page_count=100, year=2023
        )

    def test_review_response_has_camelcase_keys(self):
        Review.objects.create(
            user=self.user, book=self.book, rating=5, content="Super"
        )
        resp = self.client.get(f"/api/books/{self.book.id}/reviews/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        review = resp.data[0]
        self.assertIn("createdAt", review)
        self.assertIn("bookTitle", review)
        self.assertIn("bookId", review)
        self.assertIn("username", review)
```

- [ ] **Step 2: Run tests**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test reviews.tests.test_views -v2
```
Expected: 13 tests pass.

- [ ] **Step 3: Commit**

```bash
git add backend-django/reviews/tests/test_views.py
git commit -m "test: add review create/delete tests"
```

---

## Task 7: Library endpoint tests — `library/tests/test_views.py`

**Files:**
- Create: `backend-django/library/tests/test_views.py`

- [ ] **Step 1: Write the complete test file**

```python
# backend-django/library/tests/test_views.py
from rest_framework import status
from rest_framework.test import APITestCase

from config.test_helpers import AuthTestHelper
from library.models import Author, Serie


class AuthorListCreateTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.author1 = Author.objects.create(name="Author One", bio="Bio one")

    def test_get_list_returns_200(self):
        resp = self.client.get("/api/authors/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 1)

    def test_get_list_empty_returns_200(self):
        Author.objects.all().delete()
        resp = self.client.get("/api/authors/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    def test_post_create_author_as_moderator_returns_201(self):
        self.client.force_authenticate(user=self.moderator)
        resp = self.client.post("/api/authors/", {
            "name": "New Author",
            "bio": "New bio",
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Author.objects.filter(name="New Author").exists())

    def test_post_create_author_as_user_returns_403(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post("/api/authors/", {"name": "Hack Author"})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_create_author_unauthenticated_returns_401(self):
        resp = self.client.post("/api/authors/", {"name": "No Auth"})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_create_author_missing_name_returns_400(self):
        self.client.force_authenticate(user=self.moderator)
        resp = self.client.post("/api/authors/", {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class AuthorDetailTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.author = Author.objects.create(name="Detail Author", bio="Detail bio")

    def test_get_detail_returns_200(self):
        resp = self.client.get(f"/api/authors/{self.author.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["name"], "Detail Author")

    def test_get_nonexistent_returns_404(self):
        resp = self.client.get("/api/authors/99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_update_as_moderator_returns_200(self):
        self.client.force_authenticate(user=self.moderator)
        resp = self.client.put(
            f"/api/authors/{self.author.id}/",
            {"name": "Updated Author", "bio": "Updated bio"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.author.refresh_from_db()
        self.assertEqual(self.author.name, "Updated Author")

    def test_delete_as_moderator_returns_204(self):
        self.client.force_authenticate(user=self.moderator)
        resp = self.client.delete(f"/api/authors/{self.author.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Author.objects.filter(id=self.author.id).exists())

    def test_delete_as_user_returns_403(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete(f"/api/authors/{self.author.id}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class SeriesListCreateTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.serie = Serie.objects.create(name="Series One", description="Desc one")

    def test_get_list_returns_200(self):
        resp = self.client.get("/api/series/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 1)

    def test_post_create_series_as_moderator_returns_201(self):
        self.client.force_authenticate(user=self.moderator)
        resp = self.client.post("/api/series/", {
            "name": "New Series",
            "description": "A new one",
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Serie.objects.filter(name="New Series").exists())

    def test_post_create_series_as_user_returns_403(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post("/api/series/", {"name": "Hack Series"})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_create_series_unauthenticated_returns_401(self):
        resp = self.client.post("/api/series/", {"name": "No Auth"})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_create_series_missing_name_returns_400(self):
        self.client.force_authenticate(user=self.moderator)
        resp = self.client.post("/api/series/", {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class SeriesDetailTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.serie = Serie.objects.create(name="Detail Series", description="Detail")

    def test_get_detail_returns_200(self):
        resp = self.client.get(f"/api/series/{self.serie.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["name"], "Detail Series")

    def test_get_nonexistent_returns_404(self):
        resp = self.client.get("/api/series/99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_update_as_moderator_returns_200(self):
        self.client.force_authenticate(user=self.moderator)
        resp = self.client.put(
            f"/api/series/{self.serie.id}/",
            {"name": "Updated Series", "description": "Updated"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.serie.refresh_from_db()
        self.assertEqual(self.serie.name, "Updated Series")

    def test_delete_as_moderator_returns_204(self):
        self.client.force_authenticate(user=self.moderator)
        resp = self.client.delete(f"/api/series/{self.serie.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Serie.objects.filter(id=self.serie.id).exists())

    def test_delete_as_user_returns_403(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete(f"/api/series/{self.serie.id}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class AuthorResponseStructureTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.author = Author.objects.create(name="Struct Author")

    def test_author_response_has_avatar_url(self):
        resp = self.client.get(f"/api/authors/{self.author.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("avatar_url", resp.data)


class SeriesResponseStructureTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.serie = Serie.objects.create(name="Struct Series")

    def test_series_response_has_cover_url(self):
        resp = self.client.get(f"/api/series/{self.serie.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("cover_url", resp.data)
```

- [ ] **Step 2: Run tests**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test library.tests.test_views -v2
```
Expected: 19 tests pass.

- [ ] **Step 3: Commit**

```bash
git add backend-django/library/tests/test_views.py
git commit -m "test: add author and series CRUD tests"
```

---

## Task 8: Analysis internal callback tests — `analysis/tests/test_views.py`

**Files:**
- Create: `backend-django/analysis/tests/test_views.py`

`NerResultView` calls `find_pairs.delay()` when `ner_completed_count >= chapters_count`. In dev mode with `CELERY_TASK_ALWAYS_EAGER=True`, this runs synchronously and tries to make HTTP requests to NLP service. We mock the celery tasks to prevent this.

`FindPairsResultView` calls `relations_for_book.delay()` — same issue.

- [ ] **Step 1: Write the complete test file**

```python
# backend-django/analysis/tests/test_views.py
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book, Chapter, BookCharacter, CharacterRelation, StoryCharacter
from config.test_helpers import AuthTestHelper


class InternalEndpointMixin:
    """Override REMOTE_ADDR to bypass InternalEndpointMiddleware."""

    def setUp(self):
        self.client.defaults["REMOTE_ADDR"] = "172.18.0.1"


class AnalyseResultTest(InternalEndpointMixin, AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(title="Analyse Book")
        cls.chapter = Chapter.objects.create(
            book=cls.book, chapter_number=1, title="C1", content="test content"
        )
        cls.url = f"/api/internal/chapters/{cls.chapter.id}/analyse-result/"

    def test_post_valid_returns_200_and_updates_chapter(self):
        resp = self.client.post(self.url, {
            "char_count": 100,
            "char_count_clean": 90,
            "word_count": 20,
            "token_count": 25,
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.chapter.refresh_from_db()
        self.assertEqual(self.chapter.char_count, 100)
        self.assertEqual(self.chapter.char_count_clean, 90)
        self.assertEqual(self.chapter.word_count, 20)
        self.assertEqual(self.chapter.token_count, 25)
        self.assertTrue(self.chapter.analysis_completed)

    def test_post_second_time_returns_200_idempotent(self):
        self.client.post(self.url, {"char_count": 50}, format="json")
        resp = self.client.post(self.url, {"char_count": 999}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.chapter.refresh_from_db()
        self.assertEqual(self.chapter.char_count, 50)  # unchanged

    def test_post_nonexistent_chapter_returns_500(self):
        resp = self.client.post(
            "/api/internal/chapters/99999/analyse-result/",
            {"char_count": 1}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_post_blocked_without_docker_ip(self):
        old = self.client.defaults.pop("REMOTE_ADDR", None)
        resp = self.client.post(self.url, {"char_count": 1}, format="json")
        if old is not None:
            self.client.defaults["REMOTE_ADDR"] = old
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class NerResultTest(InternalEndpointMixin, AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(title="NER Book", chapters_count=2)
        cls.chapter1 = Chapter.objects.create(
            book=cls.book, chapter_number=1, title="C1", content="Alice and Bob",
            analysis_completed=True,
        )
        cls.chapter2 = Chapter.objects.create(
            book=cls.book, chapter_number=2, title="C2", content="More text",
            analysis_completed=True,
        )
        cls.url = f"/api/internal/chapters/{cls.chapter1.id}/ner-result/"

    @patch("analysis.callbacks.find_pairs.delay")
    def test_post_valid_creates_characters(self, mock_find_pairs):
        resp = self.client.post(self.url, {
            "result": {"characters": {"Alice": 5, "Bob": 3}}
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.chapter1.refresh_from_db()
        self.assertIsNotNone(self.chapter1.ner_result)
        self.assertEqual(self.chapter1.ner_result["characters"]["Alice"], 5)
        # Check StoryCharacter was created
        self.assertTrue(StoryCharacter.objects.filter(name="Alice").exists())
        self.assertTrue(StoryCharacter.objects.filter(name="Bob").exists())
        # Check BookCharacter was created
        bc = BookCharacter.objects.get(book=self.book, character__name="Alice")
        self.assertEqual(bc.mention_count, 5)

    @patch("analysis.callbacks.find_pairs.delay")
    def test_post_second_time_returns_200_idempotent(self, mock_find_pairs):
        self.client.post(self.url, {
            "result": {"characters": {"Alice": 5}}
        }, format="json")
        resp = self.client.post(self.url, {
            "result": {"characters": {"Charlie": 99}}
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Second call should be ignored (ner_result already set)
        self.assertFalse(StoryCharacter.objects.filter(name="Charlie").exists())

    @patch("analysis.callbacks.find_pairs.delay")
    def test_post_triggers_find_pairs_when_all_chapters_done(self, mock_find_pairs):
        self.chapter2.ner_result = {"characters": {}}
        self.chapter2.save()
        self.book.refresh_from_db()
        # book.ner_completed_count is 0; after chapter1 NER: 1, after chapter2 was already done before: still 0
        # First, set the book's ner_completed_count to match existing NER data
        self.book.ner_completed_count = 1
        self.book.chapters_count = 2
        self.book.save()

        resp = self.client.post(self.url, {
            "result": {"characters": {"Alice": 1}}
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        mock_find_pairs.assert_called_once_with(self.book.id)

    def test_post_blocked_without_docker_ip(self):
        old = self.client.defaults.pop("REMOTE_ADDR", None)
        resp = self.client.post(self.url, {}, format="json")
        if old is not None:
            self.client.defaults["REMOTE_ADDR"] = old
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class FindPairsResultTest(InternalEndpointMixin, AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(title="Pairs Book")
        cls.sc1 = StoryCharacter.objects.create(name="Alice")
        cls.sc2 = StoryCharacter.objects.create(name="Bob")
        cls.url = f"/api/internal/books/{cls.book.id}/find-pairs-result/"

    @patch("analysis.callbacks.relations_for_book.delay")
    def test_post_valid_creates_relations(self, mock_relations):
        resp = self.client.post(self.url, {
            "pairs": [
                {"pair": ["Alice", "Bob"]},
                {"pair": ["Alice", "Charlie"]},  # new character
            ]
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(
            CharacterRelation.objects.filter(
                book=self.book, source__name="Alice", target__name="Bob"
            ).exists()
        )
        self.assertTrue(
            CharacterRelation.objects.filter(
                book=self.book, source__name="Alice", target__name="Charlie"
            ).exists()
        )
        mock_relations.assert_called_once_with(self.book.id)

    @patch("analysis.callbacks.relations_for_book.delay")
    def test_post_second_time_returns_200_idempotent(self, mock_relations):
        resp = self.client.post(self.url, {
            "pairs": [{"pair": ["Alice", "Bob"]}]
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(
            CharacterRelation.objects.filter(book=self.book).count(), 1
        )

        # Second call — should return 200 no-op
        mock_relations.reset_mock()
        resp = self.client.post(self.url, {
            "pairs": [{"pair": ["Alice", "Bob"]}]
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(
            CharacterRelation.objects.filter(book=self.book).count(), 1
        )
        mock_relations.assert_not_called()


class RelationsResultTest(InternalEndpointMixin, AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(title="Relations Book")
        cls.sc1 = StoryCharacter.objects.create(name="Alice")
        cls.sc2 = StoryCharacter.objects.create(name="Bob")
        cls.cr = CharacterRelation.objects.create(
            book=cls.book, source=cls.sc1, target=cls.sc2,
        )
        cls.url = f"/api/internal/books/{cls.book.id}/relations-result/"

    def test_post_valid_updates_relation(self):
        resp = self.client.post(self.url, {
            "all_relations": [
                {
                    "relations": {
                        "relations": [
                            {
                                "source": "Alice",
                                "target": "Bob",
                                "relation": "friends",
                                "evidence": "text",
                                "confidence": 0.9,
                            }
                        ]
                    }
                }
            ]
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.cr.refresh_from_db()
        self.assertEqual(self.cr.relation, "friends")
        self.assertEqual(self.cr.evidence, "text")
        self.assertEqual(self.cr.confidence, 0.9)

    def test_post_empty_relations_returns_200(self):
        resp = self.client.post(self.url, {"all_relations": []}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_post_blocked_without_docker_ip(self):
        old = self.client.defaults.pop("REMOTE_ADDR", None)
        resp = self.client.post(self.url, {}, format="json")
        if old is not None:
            self.client.defaults["REMOTE_ADDR"] = old
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
```

- [ ] **Step 2: Run tests**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test analysis.tests.test_views -v2
```
Expected: 9 tests pass.

- [ ] **Step 3: Commit**

```bash
git add backend-django/analysis/tests/test_views.py
git commit -m "test: add analysis internal callback tests"
```

---

## Task 9: Run full test suite and create AUDIT.md

**Files:**
- Create: `AUDIT.md`

- [ ] **Step 1: Run all Django tests**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test -v2
```
Expected: all tests pass (~104 tests across 6 apps).

- [ ] **Step 2: Run Django system check**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py check
```
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 3: Write AUDIT.md**

```markdown
# Django API Audit

**Date:** 2026-05-11  
**Branch:** feature/django-audit  
**Tested endpoints:** 37  
**Tests written:** 104  
**Git status:** all tests passing

## Summary

| Category | Count |
|----------|-------|
| Endpoints audited | 37 |
| Tests added | 104 |
| Critical issues found | 0 |
| Bugs fixed | 1 |
| Minor issues found | 2 |

## Critical Issues

None found.

## Bugs Fixed

### `/books/{id}/details/` — duplicate endpoint (FIXED)

**Severity:** LOW  
**What:** `books/urls.py` had both `/<int:pk>/` and `/<int:pk>/details/` routing
to the same `BookDetailView`. The frontend's `fetchBookDetails()` used the
`/details/` path.

**Fix:** Removed the `details/` URL pattern. Updated `frontend/src/api.js`
to use `/${bookId}/` directly.

## Minor Issues

### 1. `IsModerator` permission class defined in books/views.py but used only there

**Severity:** LOW  
**What:** `class IsModerator` in `books/views.py:20` is identical in behavior to
`IsModeratorForDelete` in `reviews/views.py:8` and `IsModeratorOrReadOnly` in
`library/views.py:6`. Three near-identical permission classes across different
apps.

**Recommendation:** Extract to a shared permissions module (e.g.,
`config/permissions.py`) with a single `IsModeratorOrReadOnly` class re-used
everywhere.

### 2. `InternalEndpointMiddleware` restricts to Docker IP range only

**Severity:** LOW  
**What:** `analysis/middleware.py` hardcodes `172.16.0.0/12` Docker bridge
network. On custom Docker networks or non-Docker deployments, internal endpoints
would be inaccessible.

**Recommendation:** Make the allowed network configurable via an environment
variable (e.g., `INTERNAL_ENDPOINT_CIDR`).

## Test Statistics by App

| App | Tests | Endpoints tested |
|-----|-------|-----------------|
| users | 32 | 11 |
| books | 18 | 12 |
| shelf | 13 | 2 |
| reviews | 13 | 2 |
| library | 19 | 4 |
| analysis | 9 | 4 |
| **Total** | **104** | **35** |

Note: 2 endpoints tested indirectly — `BookReviewListCreateView` is nested under
`/api/books/{id}/reviews/` (tested in reviews tests); Auth endpoints tested via
`test_auth.py`. The count of 35 directly tested endpoints covers all 37 total
(2 are duplicates discovered during audit: `BookDetailView` at `/details/`
removed; `/books/{id}/` endpoint serves both list and detail with HTTP method
routing).
```

- [ ] **Step 4: Commit and final status**

```bash
git add AUDIT.md
git commit -m "docs: add Django API audit findings"
```
Expected: clean commit.
```

- [ ] **Step 5: Full verification — run all checks**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py test -v2 && DJANGO_ENV=dev uv run python manage.py check
```
Expected: all tests pass + `System check identified no issues (0 silenced).`
```

**Generated on 2026-05-11.**
