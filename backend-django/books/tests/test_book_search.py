from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book, BookAuthor, BookGenre
from library.models import Author, Genre

User = get_user_model()


class BookSearchTests(APITestCase):
    """Search, filter, and ordering on GET /api/books/."""

    @classmethod
    def setUpTestData(cls):
        cls.author_tolkien = Author.objects.create(name="J.R.R. Tolkien")
        cls.author_rowling = Author.objects.create(name="J.K. Rowling")
        cls.genre_fantasy = Genre.objects.create(name="fantasy")
        cls.genre_scifi = Genre.objects.create(name="science fiction")

        book1 = Book.objects.create(title="The Hobbit", year=1937, avg_rating=4.3)
        BookAuthor.objects.create(book=book1, author=cls.author_tolkien)
        BookGenre.objects.create(book=book1, genre=cls.genre_fantasy)

        book2 = Book.objects.create(title="Harry Potter", year=1997, avg_rating=4.5)
        BookAuthor.objects.create(book=book2, author=cls.author_rowling)
        BookGenre.objects.create(book=book2, genre=cls.genre_fantasy)

        book3 = Book.objects.create(title="Foundation", year=1951, avg_rating=4.1)
        BookAuthor.objects.create(book=book3, author=Author.objects.create(name="Isaac Asimov"))
        BookGenre.objects.create(book=book3, genre=cls.genre_scifi)

    def test_search_by_title(self):
        resp = self.client.get("/api/books/?search=hobbit")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["total"], 1)
        self.assertEqual(resp.data["data"][0]["title"], "The Hobbit")

    def test_filter_by_author(self):
        resp = self.client.get("/api/books/?author=Tolkien")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["total"], 1)
        self.assertEqual(resp.data["data"][0]["title"], "The Hobbit")

    def test_filter_by_genre(self):
        resp = self.client.get("/api/books/?genre=fantasy")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["total"], 2)
        titles = {b["title"] for b in resp.data["data"]}
        self.assertSetEqual(titles, {"The Hobbit", "Harry Potter"})

    def test_filter_by_year_range(self):
        resp = self.client.get("/api/books/?year_min=1950&year_max=1990")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        titles = {b["title"] for b in resp.data["data"]}
        self.assertSetEqual(titles, {"Foundation"})

    def test_ordering_by_rating_desc(self):
        resp = self.client.get("/api/books/?ordering=-avg_rating")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ratings = [b["avg_rating"] for b in resp.data["data"]]
        self.assertEqual(ratings, [4.5, 4.3, 4.1])

    def test_empty_search_results(self):
        resp = self.client.get("/api/books/?search=zzzznonexistent")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["total"], 0)
        self.assertEqual(resp.data["data"], [])
