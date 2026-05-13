from rest_framework import status
from rest_framework.test import APITestCase

from config.test_helpers import AuthTestHelper
from books.models import Book
from library.models import Author


class BookListViewTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.author = Author.objects.create(name="Test Author")
        cls.book1 = Book.objects.create(title="First Book", isbn="111", page_count=200, year=2023)
        cls.book1.authors.add(cls.author)
        cls.book1.tags.set([])
        cls.book2 = Book.objects.create(title="Second Book", isbn="222", page_count=300, year=2024)
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


class BookDetailTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.author = Author.objects.create(name="Detail Author")
        cls.book = Book.objects.create(title="Detail Book", isbn="444", page_count=250, year=2023)
        cls.book.authors.add(cls.author)
        cls.book.tags.set([])

    def test_get_detail_returns_200_with_book_and_chapters(self):
        resp = self.client.get(f"/api/books/{self.book.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("book", resp.data)
        self.assertIn("chapters", resp.data)
        self.assertIn("characters", resp.data)
        self.assertIn("relations", resp.data)
        self.assertEqual(resp.data["book"]["title"], "Detail Book")

    def test_get_nonexistent_book_returns_404(self):
        resp = self.client.get("/api/books/99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


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
