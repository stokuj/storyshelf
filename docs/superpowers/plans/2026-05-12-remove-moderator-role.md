# Remove MODERATOR Role Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the MODERATOR role from the codebase — three roles become two (USER, ADMIN).

**Architecture:** Remove MODERATOR from the User.Role TextChoices, replace all `role in ("MODERATOR", "ADMIN")` checks with `role == "ADMIN"`, rename permission classes, update tests to use `self.admin` instead of `self.moderator`, migrate existing MODERATOR users to ADMIN via data migration.

**Tech Stack:** Django 6 ORM, Django tests, Ruff linting

---

## File Structure

- Modify: `backend-django/users/models.py:26-29` — remove MODERATOR from Role TextChoices
- Modify: `backend-django/books/views.py:20-25` — rename IsModerator → IsAdmin, check only ADMIN
- Modify: `backend-django/library/views.py:6-13` — rename IsModeratorOrReadOnly → IsAdminOrReadOnly, check only ADMIN
- Modify: `backend-django/reviews/views.py:8-15` — rename IsModeratorForDelete → IsAdminForDelete, check only ADMIN
- Modify: `backend-django/config/test_helpers.py:14-19` — remove moderator, add `upgrade_moderator_to_admin` data migration helper
- Modify: `backend-django/books/tests/test_books.py` — replace `self.moderator` with `self.admin`
- Modify: `backend-django/reviews/tests/test_views.py` — replace `self.moderator` with `self.admin`
- Modify: `backend-django/library/tests/test_views.py` — replace `self.moderator` with `self.admin`
- Modify: `backend-django/shelf/tests/test_views.py` — replace `self.moderator` with `self.admin`
- Create: `backend-django/users/migrations/0002_remove_moderator_role.py` — auto-migration from makemigrations
- Create: `backend-django/users/migrations/0003_upgrade_moderator_to_admin.py` — data migration

### Task 1: Remove MODERATOR from User.Role and generate schema migration

**Files:**
- Modify: `backend-django/users/models.py:26-29`

- [ ] **Step 1: Remove MODERATOR from Role TextChoices**

```python
class Role(models.TextChoices):
    USER = "USER"
    ADMIN = "ADMIN"
```

Replace lines 26-29 in `backend-django/users/models.py`.

- [ ] **Step 2: Generate the auto-migration**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py makemigrations users --name remove_moderator_role`
Expected: Creates `backend-django/users/migrations/0002_remove_moderator_role.py`

- [ ] **Step 3: Apply migration**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py migrate`
Expected: `Applying users.0002_remove_moderator_role... OK`

- [ ] **Step 4: Commit**

```bash
git add backend-django/users/models.py backend-django/users/migrations/0002_remove_moderator_role.py
git commit -m "refactor: remove MODERATOR from User.Role choices"
```

### Task 2: Add data migration to upgrade existing MODERATOR users to ADMIN

**Files:**
- Create: `backend-django/users/migrations/0003_upgrade_moderator_to_admin.py`

- [ ] **Step 1: Create empty data migration**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py makemigrations users --empty --name upgrade_moderator_to_admin`
Expected: Creates `backend-django/users/migrations/0003_upgrade_moderator_to_admin.py`

- [ ] **Step 2: Add data migration logic**

Add this `RunPython` operation to the migration file:

```python
from django.db import migrations


def upgrade_moderator_to_admin(apps, schema_editor):
    User = apps.get_model("users", "User")
    User.objects.filter(role="MODERATOR").update(role="ADMIN")


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_remove_moderator_role"),
    ]

    operations = [
        migrations.RunPython(
            upgrade_moderator_to_admin,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
```

- [ ] **Step 3: Apply migration**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py migrate`
Expected: `Applying users.0003_upgrade_moderator_to_admin... OK`

- [ ] **Step 4: Commit**

```bash
git add backend-django/users/migrations/0003_upgrade_moderator_to_admin.py
git commit -m "refactor: data migration to upgrade MODERATOR users to ADMIN"
```

### Task 3: Update books/views.py — rename IsModerator to IsAdmin, check ADMIN only

**Files:**
- Modify: `backend-django/books/views.py:20-25`

- [ ] **Step 1: Rename class and change check**

Replace:

```python
class IsModerator(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in (
            "MODERATOR",
            "ADMIN",
        )
```

With:

```python
class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "ADMIN"
```

- [ ] **Step 2: Update all references to `IsModerator` in the same file**

`backend-django/books/views.py` uses `IsModerator()` in:
- line 36: `return [permissions.IsAuthenticated(), IsModerator()]`
- line 73: `return [permissions.IsAuthenticated(), IsModerator()]`
- line 95: `return [permissions.IsAuthenticated(), IsModerator()]`

Replace all three occurrences of `IsModerator()` with `IsAdmin()`.

- [ ] **Step 3: Run existing books tests to verify nothing broke**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test books.tests.test_books`
Expected: All tests pass (tests still use `self.moderator` from test_helpers — will be updated in Task 5)

- [ ] **Step 4: Commit**

```bash
git add backend-django/books/views.py
git commit -m "refactor: rename IsModerator to IsAdmin, check ADMIN role only"
```

### Task 4: Update library/views.py and reviews/views.py — rename permission classes

**Files:**
- Modify: `backend-django/library/views.py:6-13`
- Modify: `backend-django/reviews/views.py:8-15`

- [ ] **Step 1: Rename IsModeratorOrReadOnly → IsAdminOrReadOnly in library/views.py**

Replace:

```python
class IsModeratorOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role in (
            "MODERATOR",
            "ADMIN",
        )
```

With:

```python
class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == "ADMIN"
```

Then find and replace all `IsModeratorOrReadOnly` → `IsAdminOrReadOnly` in the file (6 occurrences — each view class's `permission_classes`).

- [ ] **Step 2: Rename IsModeratorForDelete → IsAdminForDelete in reviews/views.py**

Replace:

```python
class IsModeratorForDelete(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "DELETE":
            return request.user.is_authenticated and request.user.role in (
                "MODERATOR",
                "ADMIN",
            )
        return True
```

With:

```python
class IsAdminForDelete(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "DELETE":
            return request.user.is_authenticated and request.user.role == "ADMIN"
        return True
```

Then replace `IsModeratorForDelete` → `IsAdminForDelete` in the `ReviewDeleteView` permission_classes (line 37).

- [ ] **Step 3: Run library and reviews tests**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test library.tests.test_views reviews.tests.test_views`
Expected: Tests pass (using `self.moderator` from helpers — still valid since test_helpers creates a user with role `"MODERATOR"` which still passes auth since `IsAdminOrReadOnly` checks `role == "ADMIN"`... wait, these tests will FAIL because `self.moderator` has `role="MODERATOR"` and the new check is `role == "ADMIN"`. This is expected — the tests will be fixed in Task 5.)

Expected: Some tests may fail because `self.moderator` role is now `"MODERATOR"` not `"ADMIN"`. This is fine — fixed in Task 5.

- [ ] **Step 4: Commit**

```bash
git add backend-django/library/views.py backend-django/reviews/views.py
git commit -m "refactor: rename Moderator permission classes to Admin, check ADMIN only"
```

### Task 5: Update test_helpers and all test files — replace moderator with admin

**Files:**
- Modify: `backend-django/config/test_helpers.py:14-19`
- Modify: `backend-django/books/tests/test_books.py`
- Modify: `backend-django/reviews/tests/test_views.py`
- Modify: `backend-django/library/tests/test_views.py`
- Modify: `backend-django/shelf/tests/test_views.py`

- [ ] **Step 1: Remove moderator from test_helpers, keep only user and admin**

Replace lines 8-25 of `backend-django/config/test_helpers.py`:

```python
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
        cls.admin = User.objects.create_user(
            email="admin@test.com",
            username="admin",
            password="password123",
            role="ADMIN",
        )
```

Removes the `cls.moderator` attribute entirely.

- [ ] **Step 2: Replace self.moderator with self.admin in books/tests/test_books.py**

Find every `self.moderator` and replace with `self.admin` (13 occurrences across lines 44, 85, 90, 127, 144, 181, 200, 208).
Also rename test method names: `as_moderator` → `as_admin` in methods like `test_post_create_book_as_moderator_returns_201`.

Example replacement:
```python
# Before:
def test_post_create_book_as_moderator_returns_201(self):
    self.client.force_authenticate(user=self.moderator)

# After:
def test_post_create_book_as_admin_returns_201(self):
    self.client.force_authenticate(user=self.admin)
```

- [ ] **Step 3: Replace self.moderator with self.admin in reviews/tests/test_views.py**

Replace `self.moderator` → `self.admin` (3 occurrences at lines 114, 134).
Rename `test_delete_review_as_moderator_returns_204` → `test_delete_review_as_admin_returns_204`.

- [ ] **Step 4: Replace self.moderator with self.admin in library/tests/test_views.py**

Replace `self.moderator` → `self.admin` (10 occurrences at lines 26, 47, 68, 78, 101, 122, 143, 153).
Rename `as_moderator` → `as_admin` in test method names.

- [ ] **Step 5: Replace self.moderator with self.admin in shelf/tests/test_views.py**

Replace `self.moderator` → `self.admin` (2 occurrences at lines 38, 121).

- [ ] **Step 6: Run all tests to verify**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test`
Expected: All tests pass.

- [ ] **Step 7: Commit**

```bash
git add backend-django/config/test_helpers.py backend-django/books/tests/test_books.py backend-django/reviews/tests/test_views.py backend-django/library/tests/test_views.py backend-django/shelf/tests/test_views.py
git commit -m "test: replace moderator with admin in test_helpers and test files"
```

### Task 6: Lint and final verification

**Files:**
- None new — verify all previous changes

- [ ] **Step 1: Run Ruff lint**

Run: `cd backend-django && uv run ruff check .`
Expected: All checks pass, no errors.

- [ ] **Step 2: Run full test suite**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test`
Expected: All tests pass.

- [ ] **Step 3: Run makemigrations dry-run to confirm no pending changes**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py makemigrations --check --dry-run`
Expected: `No changes detected`

- [ ] **Step 4: Commit (if any lint fixes were needed)**

```bash
git add backend-django/
git commit -m "chore: post-refactor lint and final verification"
```
