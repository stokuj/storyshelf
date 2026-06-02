from django.test import TestCase
from rest_framework.test import APIClient

from books.models import Book
from library.models import Author, Genre


class BookFiltersTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        fantasy = Genre.objects.create(name="Fantasy")
        scifi = Genre.objects.create(name="Sci-Fi")

        self.book_fantasy = Book.objects.create(title="A Fantasy Book", avg_rating=4.5)
        self.book_fantasy.genres.add(fantasy)

        self.book_scifi = Book.objects.create(title="A Sci-Fi Book", avg_rating=3.0)
        self.book_scifi.genres.add(scifi)

        self.book_both = Book.objects.create(title="Sci-Fi Fantasy", avg_rating=5.0)
        self.book_both.genres.add(fantasy, scifi)

    def test_filter_by_genre(self):
        response = self.client.get("/api/books/?genre=Fantasy")
        self.assertEqual(response.status_code, 200)
        ids = [b["id"] for b in response.data["data"]]
        self.assertIn(self.book_fantasy.pk, ids)
        self.assertIn(self.book_both.pk, ids)
        self.assertNotIn(self.book_scifi.pk, ids)

    def test_filter_genre_case_insensitive(self):
        response = self.client.get("/api/books/?genre=fantasy")
        self.assertEqual(response.status_code, 200)
        ids = [b["id"] for b in response.data["data"]]
        self.assertIn(self.book_fantasy.pk, ids)

    def test_sort_by_rating(self):
        response = self.client.get("/api/books/?ordering=-avg_rating")
        self.assertEqual(response.status_code, 200)
        ratings = [b["avg_rating"] for b in response.data["data"]]
        self.assertEqual(ratings, sorted(ratings, reverse=True))

    def test_sort_by_recent(self):
        response = self.client.get("/api/books/?ordering=-year")
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.data)

    def test_invalid_sort_falls_back_to_title(self):
        response = self.client.get("/api/books/?ordering=garbage")
        self.assertEqual(response.status_code, 200)
        titles = [b["title"] for b in response.data["data"]]
        self.assertEqual(titles, sorted(titles))

    def test_combined_filters(self):
        response = self.client.get("/api/books/?genre=Fantasy&ordering=-avg_rating&search=Fantasy")
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.data)

    def test_author_filter_does_not_duplicate_multi_author_books(self):
        # A book whose authors both match the query must appear exactly once,
        # and the paginated `total` must not be inflated by the M2M join.
        book = Book.objects.create(title="Good Omens")
        book.authors.add(
            Author.objects.create(name="Terry Pratchett"),
            Author.objects.create(name="Neil Gaiman (with Terry)"),
        )
        response = self.client.get("/api/books/?author=terry")
        self.assertEqual(response.status_code, 200)
        ids = [b["id"] for b in response.data["data"]]
        self.assertEqual(ids.count(book.pk), 1)
        self.assertEqual(response.data["total"], 1)

    def test_paginated_shape(self):
        response = self.client.get("/api/books/")
        self.assertEqual(response.status_code, 200)
        for key in ("data", "page", "per_page", "total"):
            self.assertIn(key, response.data)
