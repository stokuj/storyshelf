# Django Backend Audit — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Naprawić integralność modeli, lint, walidację i pokrycie testami w backend-django/.

**Architecture:** Zmiany w modelach Django (constraints, validators, clean()), konfiguracja ruff per-file-ignores, walidacja w serializatorze, nowe testy. Baza danych resetowana po zmianach modeli — bez ręcznych migracji.

**Tech Stack:** Django 6, DRF 3.17, pytest-django, ruff, uv

---

## Pliki do zmiany

| Plik | Zmiana |
|---|---|
| `books/models.py` | `isbn` unique+nullable, `title` wymagany, `year`/`page_count` MinValueValidator |
| `library/models.py` | `Author.name` unique |
| `shelf/models.py` | `ShelfEntry.clean()`, `db_index` na FK |
| `reviews/models.py` | `db_index` na FK |
| `reviews/serializers.py` | walidacja istnienia `book_id` |
| `config/settings/base.py` | rozbij `SPECTACULAR_SETTINGS` na wiele linii |
| `pyproject.toml` | `per-file-ignores`, `pytest-cov` w dev deps, coverage config |
| `reviews/tests/test_signals.py` | NOWY — testy sygnału `avg_rating` |
| `library/tests/test_views.py` | dodaj testy `GenreListView` / `GenreRetrieveView` |
| `shelf/tests/test_views.py` | dodaj testy `ShelfEntry.clean()` przez API |

---

## Task 1: Napraw Book model

**Files:**
- Modify: `books/models.py`

- [ ] **Krok 1: Napisz testy modelu**

Dodaj nowy plik `books/tests/test_models.py`:

```python
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework.test import APITestCase

from books.models import Book


class BookIsbnUniqueTest(APITestCase):
    def test_duplicate_isbn_raises_integrity_error(self):
        Book.objects.create(title="Book A", isbn="978-0-123", year=2020, page_count=100)
        with self.assertRaises(IntegrityError):
            Book.objects.create(title="Book B", isbn="978-0-123", year=2021, page_count=200)

    def test_two_books_without_isbn_allowed(self):
        Book.objects.create(title="Book A", isbn=None, year=2020, page_count=100)
        Book.objects.create(title="Book B", isbn=None, year=2021, page_count=200)
        self.assertEqual(Book.objects.filter(isbn__isnull=True).count(), 2)


class BookValidatorsTest(APITestCase):
    def test_year_below_1_raises_validation_error(self):
        book = Book(title="Bad Year", isbn="111", year=0, page_count=100)
        with self.assertRaises(ValidationError):
            book.full_clean()

    def test_page_count_below_1_raises_validation_error(self):
        book = Book(title="No Pages", isbn="222", year=2020, page_count=0)
        with self.assertRaises(ValidationError):
            book.full_clean()

    def test_valid_book_passes_full_clean(self):
        book = Book(title="Good Book", isbn="333", year=2020, page_count=300)
        book.full_clean()  # nie powinno rzucić
```

- [ ] **Krok 2: Uruchom testy — upewnij się że failują**

```bash
cd backend-django
DJANGO_ENV=dev uv run python manage.py test books.tests.test_models -v 2
```
Oczekiwane: błędy (testy nie przechodzą bo model jeszcze nie zmieniony).

- [ ] **Krok 3: Zmień `books/models.py`**

```python
from django.core.validators import MinValueValidator
from django.db import models


class Chapter(models.Model):
    book = models.ForeignKey("Book", on_delete=models.CASCADE, related_name="chapters")
    chapter_number = models.IntegerField()
    title = models.CharField(max_length=150, blank=True, default="")
    text = models.TextField()
    analysis_completed = models.BooleanField(default=False)
    char_count = models.IntegerField(null=True, blank=True)
    char_count_clean = models.IntegerField(null=True, blank=True)
    word_count = models.IntegerField(null=True, blank=True)
    token_count = models.IntegerField(null=True, blank=True)
    ner_pending = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ("chapter_number",)


class Book(models.Model):
    serie = models.ForeignKey(
        "library.Serie",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="books",
    )
    title = models.CharField(max_length=500)
    year = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    isbn = models.CharField(max_length=20, unique=True, null=True, blank=True, default=None)
    description = models.TextField(blank=True, default="")
    page_count = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    position_in_series = models.IntegerField(null=True, blank=True)
    chapters_count = models.IntegerField(default=0)
    ner_completed_count = models.IntegerField(default=0)
    avg_rating = models.FloatField(default=0.0)
    ratings_count = models.IntegerField(default=0)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    authors = models.ManyToManyField("library.Author", through="BookAuthor")
    tags = models.ManyToManyField("library.Tag", through="BookTag")
    genres = models.ManyToManyField("library.Genre", through="BookGenre", related_name="books")


class BookAuthor(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    author = models.ForeignKey("library.Author", on_delete=models.CASCADE)
    role = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        unique_together = ("book", "author")


class BookTag(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    tag = models.ForeignKey("library.Tag", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("book", "tag")


class BookGenre(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="book_genres")
    genre = models.ForeignKey("library.Genre", on_delete=models.CASCADE, related_name="book_genres")

    class Meta:
        unique_together = ["book", "genre"]
```

- [ ] **Krok 4: Zaktualizuj istniejące testy książek — dodaj `page_count` gdzie brakuje**

W `books/tests/test_books.py` wszystkie `Book.objects.create(...)` muszą mieć `page_count >= 1` i `year >= 1`. Sprawdź i popraw (już są `page_count=200`, `year=2023` itp. — powinno być ok).

- [ ] **Krok 5: Utwórz migrację i zresetuj bazę**

```bash
cd backend-django
uv run python manage.py makemigrations books
```

Jeśli migrate się wysypie na istniejących danych (np. isbn="" zamiast NULL): zresetuj bazę i migruj od zera:
```bash
DJANGO_ENV=dev uv run python manage.py flush --no-input
DJANGO_ENV=dev uv run python manage.py migrate
```

- [ ] **Krok 6: Uruchom testy — upewnij się że przechodzą**

```bash
DJANGO_ENV=dev uv run python manage.py test books -v 2
```
Oczekiwane: wszystkie PASS.

- [ ] **Krok 7: Commit**

```bash
git add books/models.py books/tests/test_models.py books/migrations/
git commit -m "feat: add isbn unique, MinValueValidator on year/page_count, title required"
```

---

## Task 2: Napraw Author model

**Files:**
- Modify: `library/models.py`

- [ ] **Krok 1: Napisz test unikalności**

Dodaj do `library/tests/test_views.py` na końcu pliku:

```python
class AuthorNameUniqueTest(APITestCase):
    def test_duplicate_author_name_raises_integrity_error(self):
        from django.db import IntegrityError
        Author.objects.create(name="Jane Austen")
        with self.assertRaises(IntegrityError):
            Author.objects.create(name="Jane Austen")
```

- [ ] **Krok 2: Uruchom test — upewnij się że failuje**

```bash
DJANGO_ENV=dev uv run python manage.py test library.tests.test_views.AuthorNameUniqueTest -v 2
```
Oczekiwane: FAIL.

- [ ] **Krok 3: Zmień `library/models.py`**

```python
from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=255, unique=True)
    bio = models.TextField(blank=True, default="")
    birth_date = models.DateField(null=True, blank=True)


class Serie(models.Model):  # "Series" clashes with Django test internals
    class Status(models.TextChoices):
        ONGOING = "ONGOING"
        COMPLETED = "COMPLETED"
        CANCELLED = "CANCELLED"
        HIATUS = "HIATUS"

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "series"


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
```

- [ ] **Krok 4: Migracja**

```bash
uv run python manage.py makemigrations library
DJANGO_ENV=dev uv run python manage.py migrate
```

- [ ] **Krok 5: Uruchom testy**

```bash
DJANGO_ENV=dev uv run python manage.py test library -v 2
```
Oczekiwane: wszystkie PASS.

- [ ] **Krok 6: Commit**

```bash
git add library/models.py library/tests/test_views.py library/migrations/
git commit -m "feat: add unique constraint to Author.name"
```

---

## Task 3: Napraw ShelfEntry — clean() i db_index

**Files:**
- Modify: `shelf/models.py`
- Modify: `shelf/tests/test_views.py`

- [ ] **Krok 1: Napisz testy walidacji dat**

Dodaj na końcu `shelf/tests/test_views.py`:

```python
class ShelfEntryDateValidationTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(title="Date Book", year=2020, page_count=100)

    def test_finish_before_start_returns_400(self):
        self.client.force_authenticate(user=self.user)
        ShelfEntry.objects.filter(user=self.user, book=self.book).delete()
        self.client.post(f"/api/shelf/{self.book.id}/", {"status": "READING"})
        resp = self.client.patch(
            f"/api/shelf/{self.book.id}/",
            {"status": "READ", "start_date": "2024-06-01", "finish_date": "2024-05-01"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_finish_equals_start_is_valid(self):
        self.client.force_authenticate(user=self.user)
        ShelfEntry.objects.filter(user=self.user, book=self.book).delete()
        self.client.post(f"/api/shelf/{self.book.id}/", {"status": "READING"})
        resp = self.client.patch(
            f"/api/shelf/{self.book.id}/",
            {"status": "READ", "start_date": "2024-06-01", "finish_date": "2024-06-01"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
```

- [ ] **Krok 2: Uruchom testy — upewnij się że failują**

```bash
DJANGO_ENV=dev uv run python manage.py test shelf.tests.test_views.ShelfEntryDateValidationTest -v 2
```
Oczekiwane: FAIL (brak walidacji).

- [ ] **Krok 3: Zmień `shelf/models.py`**

```python
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


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
    personal_rating = models.IntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "book")
        ordering = ("-created_at",)

    def clean(self):
        if self.start_date and self.finish_date and self.finish_date < self.start_date:
            raise ValidationError({"finish_date": "finish_date cannot be before start_date."})
```

- [ ] **Krok 4: Zaktualizuj `shelf/views.py` — wywołaj `full_clean()` w PATCH**

W `ShelfEntryView.patch()` dodaj wywołanie `full_clean()` przed `save()`:

```python
def patch(self, request, book_id):
    entry = get_object_or_404(ShelfEntry, user=request.user, book_id=book_id)
    status_val = request.data.get("status")
    if not status_val:
        return Response({"detail": "status required"}, status=400)
    entry.status = status_val
    entry.start_date = request.data.get("start_date", entry.start_date)
    entry.finish_date = request.data.get("finish_date", entry.finish_date)
    try:
        entry.full_clean()
    except ValidationError as e:
        return Response(e.message_dict, status=400)
    entry.save()
    return Response(ShelfEntrySerializer(entry).data)
```

Dodaj import na górze `shelf/views.py`:
```python
from django.core.exceptions import ValidationError
```

- [ ] **Krok 5: Migracja**

```bash
uv run python manage.py makemigrations shelf
DJANGO_ENV=dev uv run python manage.py migrate
```

- [ ] **Krok 6: Uruchom testy**

```bash
DJANGO_ENV=dev uv run python manage.py test shelf -v 2
```
Oczekiwane: wszystkie PASS.

- [ ] **Krok 7: Commit**

```bash
git add shelf/models.py shelf/views.py shelf/tests/test_views.py shelf/migrations/
git commit -m "feat: add ShelfEntry.clean() date validation and db_index on FK fields"
```

---

## Task 4: Dodaj db_index na Review FK

**Files:**
- Modify: `reviews/models.py`

- [ ] **Krok 1: Zmień `reviews/models.py`**

```python
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Review(models.Model):
    book = models.ForeignKey(
        "books.Book", on_delete=models.CASCADE, related_name="reviews", db_index=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    content = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("book", "user")
        ordering = ("-created_at",)
```

- [ ] **Krok 2: Migracja**

```bash
uv run python manage.py makemigrations reviews
DJANGO_ENV=dev uv run python manage.py migrate
```

- [ ] **Krok 3: Uruchom testy**

```bash
DJANGO_ENV=dev uv run python manage.py test reviews -v 2
```
Oczekiwane: wszystkie PASS.

- [ ] **Krok 4: Commit**

```bash
git add reviews/models.py reviews/migrations/
git commit -m "feat: add db_index on Review.book and Review.user FK fields"
```

---

## Task 5: Napraw ReviewCreateSerializer — walidacja book_id

**Files:**
- Modify: `reviews/serializers.py`
- Modify: `reviews/tests/test_views.py`

- [ ] **Krok 1: Napisz test**

Dodaj do `ReviewCreateTest` w `reviews/tests/test_views.py`:

```python
def test_post_review_nonexistent_book_returns_400(self):
    self.client.force_authenticate(user=self.user)
    resp = self.client.post(
        "/api/reviews/",
        {"bookId": 99999, "rating": 3, "content": "Ghost book"},
    )
    self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
```

- [ ] **Krok 2: Uruchom test — upewnij się że failuje**

```bash
DJANGO_ENV=dev uv run python manage.py test reviews.tests.test_views.ReviewCreateTest.test_post_review_nonexistent_book_returns_400 -v 2
```
Oczekiwane: FAIL (zwraca 500 lub inny błąd).

- [ ] **Krok 3: Zmień `reviews/serializers.py`**

```python
from rest_framework import serializers

from books.models import Book
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    bookTitle = serializers.CharField(source="book.title", read_only=True)  # noqa: N815
    bookId = serializers.IntegerField(source="book.id", read_only=True)  # noqa: N815
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)  # noqa: N815

    class Meta:
        model = Review
        fields = (
            "id",
            "username",
            "rating",
            "content",
            "createdAt",
            "bookTitle",
            "bookId",
        )
        read_only_fields = ("id", "username", "bookTitle", "bookId", "createdAt")


class ReviewCreateSerializer(serializers.ModelSerializer):
    bookId = serializers.IntegerField(source="book_id")  # noqa: N815

    class Meta:
        model = Review
        fields = ("id", "rating", "content", "bookId")
        read_only_fields = ("id",)

    def validate(self, data):
        user = self.context["request"].user
        book_id = data.get("book_id")
        if not Book.objects.filter(id=book_id).exists():
            raise serializers.ValidationError({"bookId": "Book with this id does not exist."})
        if self.instance is None and Review.objects.filter(user=user, book_id=book_id).exists():
            raise serializers.ValidationError("You have already reviewed this book.")
        return data
```

- [ ] **Krok 4: Uruchom testy**

```bash
DJANGO_ENV=dev uv run python manage.py test reviews -v 2
```
Oczekiwane: wszystkie PASS.

- [ ] **Krok 5: Commit**

```bash
git add reviews/serializers.py reviews/tests/test_views.py
git commit -m "fix: return 400 instead of 500 when reviewing non-existent book"
```

---

## Task 6: Napraw lint

**Files:**
- Modify: `pyproject.toml`
- Modify: `config/settings/base.py`

- [ ] **Krok 1: Uruchom auto-fix importów**

```bash
cd backend-django
uv run ruff check --fix .
```

- [ ] **Krok 2: Dodaj `per-file-ignores` do `pyproject.toml`**

W sekcji `[tool.ruff.lint]` zmień na:

```toml
[tool.ruff.lint]
select = ["E", "F", "I", "N"]

[tool.ruff.lint.per-file-ignores]
"*/migrations/*" = ["E501"]
"*/serializers.py" = ["N815"]
"users/serializers.py" = ["N815"]
```

- [ ] **Krok 3: Rozbij `SPECTACULAR_SETTINGS` w `config/settings/base.py`**

```python
SPECTACULAR_SETTINGS = {
    "TITLE": "StoryShelf API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}
```

- [ ] **Krok 4: Sprawdź ruff — 0 błędów**

```bash
uv run ruff check .
```
Oczekiwane: brak outputu (exit 0).

- [ ] **Krok 5: Uruchom wszystkie testy**

```bash
DJANGO_ENV=dev uv run python manage.py test -v 2
```
Oczekiwane: wszystkie PASS.

- [ ] **Krok 6: Commit**

```bash
git add pyproject.toml config/settings/base.py
git add $(git diff --name-only)
git commit -m "chore: fix all ruff lint violations (imports, E501 per-file, N815 noqa)"
```

---

## Task 7: Dodaj pytest-cov i brakujące testy

**Files:**
- Modify: `pyproject.toml`
- Create: `reviews/tests/test_signals.py`
- Modify: `library/tests/test_views.py`

- [ ] **Krok 1: Dodaj `pytest-cov` do `pyproject.toml`**

W sekcji `[dependency-groups] dev`:

```toml
[dependency-groups]
dev = [
    "pytest>=9.0.3",
    "pytest-django>=4.12.0",
    "pytest-cov>=6.0",
    "ruff>=0.15.12",
]
```

Dodaj konfigurację pytest i coverage:

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
django_db_setup = true

[tool.coverage.run]
source = ["."]
omit = ["*/migrations/*", "*/.venv/*", "*/tests/*", "manage.py", "conftest.py"]

[tool.coverage.report]
show_missing = true
skip_covered = false
```

- [ ] **Krok 2: Zainstaluj nowe zależności**

```bash
uv sync
```

- [ ] **Krok 3: Utwórz `reviews/tests/test_signals.py`**

```python
from rest_framework.test import APITestCase

from books.models import Book
from config.test_helpers import AuthTestHelper
from reviews.models import Review


class AvgRatingSignalTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(title="Signal Book", year=2020, page_count=100)

    def test_avg_rating_updates_on_review_create(self):
        Review.objects.create(user=self.user, book=self.book, rating=4, content="Good")
        self.book.refresh_from_db()
        self.assertEqual(self.book.avg_rating, 4.0)
        self.assertEqual(self.book.ratings_count, 1)

    def test_avg_rating_updates_on_second_review(self):
        from users.models import User

        user2 = User.objects.create_user(
            email="signal2@test.com", username="signaluser", password="pass123"
        )
        Review.objects.create(user=self.user, book=self.book, rating=4, content="Good")
        Review.objects.create(user=user2, book=self.book, rating=2, content="Bad")
        self.book.refresh_from_db()
        self.assertEqual(self.book.avg_rating, 3.0)
        self.assertEqual(self.book.ratings_count, 2)

    def test_avg_rating_updates_on_review_delete(self):
        review = Review.objects.create(user=self.user, book=self.book, rating=5, content="Great")
        review.delete()
        self.book.refresh_from_db()
        self.assertEqual(self.book.avg_rating, 0.0)
        self.assertEqual(self.book.ratings_count, 0)
```

- [ ] **Krok 4: Dodaj testy Genre do `library/tests/test_views.py`**

Dodaj na końcu pliku (po `SeriesResponseStructureTest`):

```python
class GenreListViewTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        from library.models import Genre
        cls.genre = Genre.objects.create(name="Fantasy")

    def test_get_list_returns_200_with_array(self):
        resp = self.client.get("/api/genres/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsInstance(resp.data, list)
        self.assertGreaterEqual(len(resp.data), 1)

    def test_get_list_sorted_alphabetically(self):
        from library.models import Genre
        Genre.objects.create(name="Adventure")
        resp = self.client.get("/api/genres/")
        names = [g["name"] for g in resp.data]
        self.assertEqual(names, sorted(names))


class GenreRetrieveViewTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        from library.models import Genre
        cls.genre = Genre.objects.create(name="Horror")

    def test_get_detail_returns_200(self):
        resp = self.client.get(f"/api/genres/{self.genre.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["name"], "Horror")

    def test_get_nonexistent_returns_404(self):
        resp = self.client.get("/api/genres/99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
```

- [ ] **Krok 5: Uruchom wszystkie testy**

```bash
DJANGO_ENV=dev uv run python manage.py test -v 2
```
Oczekiwane: wszystkie PASS (liczba testów wzrośnie).

- [ ] **Krok 6: Sprawdź pokrycie**

```bash
DJANGO_ENV=dev uv run python -m pytest --cov --cov-report=term-missing analysis/tests/
```

- [ ] **Krok 7: Commit**

```bash
git add pyproject.toml reviews/tests/test_signals.py library/tests/test_views.py
git commit -m "test: add pytest-cov, avg_rating signal tests, Genre endpoint tests"
```

---

## Weryfikacja końcowa

```bash
# Lint — 0 błędów
cd backend-django && uv run ruff check .

# Wszystkie testy zielone
DJANGO_ENV=dev uv run python manage.py test

# System check bez błędów
uv run python manage.py check

# Migracje aktualne
DJANGO_ENV=dev uv run python manage.py migrate --check

# Pokrycie
DJANGO_ENV=dev uv run python -m pytest --cov --cov-report=term-missing analysis/tests/
```
