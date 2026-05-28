from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book
from config.test_helpers import AuthTestHelper
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

    def test_get_list_returns_200_paginated(self):
        resp = self.client.get("/api/books/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for key in ("data", "page", "per_page", "total"):
            self.assertIn(key, resp.data)
        self.assertGreaterEqual(resp.data["total"], 2)

    def test_get_list_with_search_returns_filtered(self):
        resp = self.client.get("/api/books/?search=First")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        titles = [b["title"] for b in resp.data["data"]]
        self.assertIn("First Book", titles)

    def test_get_list_with_nonexistent_query_returns_empty(self):
        resp = self.client.get("/api/books/?search=zzzzzzz")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["data"], [])
        self.assertEqual(resp.data["total"], 0)


class BookDetailTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.author = Author.objects.create(name="Detail Author")
        cls.book = Book.objects.create(title="Detail Book", isbn="444", page_count=250, year=2023)
        cls.book.authors.add(cls.author)
        cls.book.tags.set([])

    def test_get_detail_returns_200_with_book_data(self):
        resp = self.client.get(f"/api/books/{self.book.slug}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["title"], "Detail Book")
        self.assertIn("authors", resp.data)
        self.assertIn("genres", resp.data)

    def test_get_nonexistent_book_returns_404(self):
        resp = self.client.get("/api/books/this-slug-does-not-exist/")
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
        resp = self.client.get("/api/books/?search=austen")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["total"], 1)
        self.assertEqual(resp.data["data"][0]["title"], "Pride")
