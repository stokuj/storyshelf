from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book, BookAuthor, BookGenre
from library.models import Author, Genre, Tag

User = get_user_model()


class BookListEmptyTest(APITestCase):
    """GET /api/books/ — empty database (paginated)."""

    def test_list_returns_paginated_empty(self):
        resp = self.client.get("/api/books/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["data"], [])
        self.assertEqual(resp.data["page"], 1)
        self.assertEqual(resp.data["per_page"], 12)
        self.assertEqual(resp.data["total"], 0)


class BookCRUDTests(APITestCase):
    """CRUD operations on /api/books/ and /api/books/{slug}/."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            handle="admin", email="admin@test.com", password="secret"
        )
        cls.author = Author.objects.create(name="J.R.R. Tolkien")
        cls.genre = Genre.objects.create(name="fantasy")

    def setUp(self):
        self.client.force_authenticate(user=self.admin)

    def test_create_simple_book(self):
        payload = {
            "title": "The Hobbit",
            "year": 1937,
            "isbn": "978-0007458424",
            "description": "A hobbit's adventure.",
            "page_count": 310,
            "cover_url": "https://example.com/cover.jpg",
            "authors": ["J.R.R. Tolkien"],
            "genres": ["fantasy"],
            "tags": ["classic"],
        }
        resp = self.client.post("/api/books/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["title"], "The Hobbit")
        self.assertEqual(resp.data["slug"], "the-hobbit")
        self.assertEqual(resp.data["year"], 1937)

    def test_create_with_nested_m2m_creates_relations(self):
        payload = {
            "title": "New Book",
            "authors": ["Author One"],
            "genres": ["fiction"],
            "tags": ["tag-one"],
            "year": 2020,
        }
        resp = self.client.post("/api/books/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        book = Book.objects.get(slug="new-book")
        self.assertEqual(book.authors.count(), 1)
        self.assertEqual(book.authors.first().name, "Author One")
        self.assertEqual(book.genres.first().name, "fiction")
        self.assertEqual(book.tags.first().name, "tag-one")

    def test_create_duplicate_title_gets_unique_slug(self):
        self.client.post("/api/books/", {"title": "Same Title"}, format="json")
        resp = self.client.post("/api/books/", {"title": "Same Title"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["slug"], "same-title-1")

    def test_list_returns_paginated_books(self):
        Book.objects.create(title="Book A", year=2000)
        Book.objects.create(title="Book B", year=2001)
        resp = self.client.get("/api/books/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["total"], 2)
        self.assertEqual(len(resp.data["data"]), 2)

    def test_detail_returns_full_book(self):
        book = Book.objects.create(
            title="The Hobbit",
            year=1937,
            isbn="978-0007458424",
            description="Adventure.",
            page_count=310,
        )
        BookAuthor.objects.create(book=book, author=self.author)
        BookGenre.objects.create(book=book, genre=self.genre)
        resp = self.client.get(f"/api/books/{book.slug}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["title"], "The Hobbit")
        self.assertEqual(resp.data["authors"], ["J.R.R. Tolkien"])
        self.assertEqual(resp.data["genres"], ["fantasy"])
        self.assertIn("created_at", resp.data)
        self.assertIn("updated_at", resp.data)

    def test_detail_nonexistent_returns_404(self):
        resp = self.client.get("/api/books/nonexistent-slug/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_updates_fields(self):
        book = Book.objects.create(title="Old Title", year=2000)
        payload = {"title": "New Title", "year": 2024}
        resp = self.client.patch(f"/api/books/{book.slug}/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["title"], "New Title")
        self.assertEqual(resp.data["year"], 2024)

    def test_delete_removes_book(self):
        book = Book.objects.create(title="To Delete")
        resp = self.client.delete(f"/api/books/{book.slug}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Book.objects.filter(slug="to-delete").exists())


class BookNestedM2MTests(APITestCase):
    """Nested M2M creation/update behavior."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            handle="admin2", email="admin2@test.com", password="secret"
        )

    def setUp(self):
        self.client.force_authenticate(user=self.admin)

    def test_creates_new_author_genre_tag(self):
        payload = {
            "title": "M2M Test",
            "authors": ["New Author"],
            "genres": ["new-genre"],
            "tags": ["new-tag"],
        }
        resp = self.client.post("/api/books/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Author.objects.filter(name="New Author").exists())
        self.assertTrue(Genre.objects.filter(name="new-genre").exists())
        self.assertTrue(Tag.objects.filter(name="new-tag").exists())

    def test_case_insensitive_merge_authors(self):
        Author.objects.create(name="J.R.R. Tolkien")
        payload = {
            "title": "Merge Test",
            "authors": ["j.r.r. tolkien"],
        }
        resp = self.client.post("/api/books/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Author.objects.filter(name__iexact="J.R.R. Tolkien").count(), 1)

    def test_patch_replaces_m2m_relations(self):
        book = Book.objects.create(title="Replace Test")
        author_a = Author.objects.create(name="Author A")
        Author.objects.create(name="Author B")
        BookAuthor.objects.create(book=book, author=author_a)
        payload = {
            "authors": ["Author B"],
            "genres": [],
            "tags": [],
        }
        resp = self.client.patch(f"/api/books/{book.slug}/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        book.refresh_from_db()
        self.assertEqual(book.authors.count(), 1)
        self.assertEqual(book.authors.first().name, "Author B")
        self.assertEqual(book.genres.count(), 0)
        self.assertEqual(book.tags.count(), 0)


class BookPermissionTests(APITestCase):
    """Permission: GET public, write methods require admin."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            handle="admin3", email="admin3@test.com", password="secret"
        )

    def test_anonymous_can_get_list(self):
        Book.objects.create(title="Public Book")
        resp = self.client.get("/api/books/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_anonymous_cannot_post(self):
        payload = {"title": "Unauthorized"}
        resp = self.client.post("/api/books/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_anonymous_cannot_delete(self):
        book = Book.objects.create(title="No Delete")
        resp = self.client.delete(f"/api/books/{book.slug}/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class BookValidationTests(APITestCase):
    """Serializer/model validation edge cases."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            handle="admin4", email="admin4@test.com", password="secret"
        )

    def setUp(self):
        self.client.force_authenticate(user=self.admin)

    def test_year_below_1_is_invalid(self):
        payload = {"title": "Bad Year", "year": 0}
        resp = self.client.post("/api/books/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("year", resp.data)

    def test_isbn_too_long_invalid(self):
        payload = {"title": "Long ISBN", "isbn": "x" * 21}
        resp = self.client.post("/api/books/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("isbn", resp.data)

    def test_missing_title_is_invalid(self):
        payload = {"year": 2020}
        resp = self.client.post("/api/books/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", resp.data)
