from django.test import TestCase
from rest_framework.test import APIClient

from books.models import Book
from library.models import Genre


class BookFiltersTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        fantasy = Genre.objects.create(name="Fantasy")
        scifi = Genre.objects.create(name="Sci-Fi")

        self.book_fantasy = Book.objects.create(
            title="A Fantasy Book", avg_rating=4.5, ratings_count=100
        )
        self.book_fantasy.genres.add(fantasy)

        self.book_scifi = Book.objects.create(
            title="A Sci-Fi Book", avg_rating=3.0, ratings_count=200
        )
        self.book_scifi.genres.add(scifi)

        self.book_both = Book.objects.create(
            title="Sci-Fi Fantasy", avg_rating=5.0, ratings_count=50
        )
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
        response = self.client.get("/api/books/?sort=rating")
        self.assertEqual(response.status_code, 200)
        ratings = [b["avg_rating"] for b in response.data["data"]]
        self.assertEqual(ratings, sorted(ratings, reverse=True))

    def test_sort_by_popular(self):
        response = self.client.get("/api/books/?sort=popular")
        self.assertEqual(response.status_code, 200)
        counts = [b["ratings_count"] for b in response.data["data"]]
        self.assertEqual(counts, sorted(counts, reverse=True))

    def test_sort_by_recent(self):
        response = self.client.get("/api/books/?sort=recent")
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.data)

    def test_invalid_sort_falls_back_to_title(self):
        response = self.client.get("/api/books/?sort=garbage")
        self.assertEqual(response.status_code, 200)
        titles = [b["title"] for b in response.data["data"]]
        self.assertEqual(titles, sorted(titles))

    def test_combined_filters(self):
        response = self.client.get("/api/books/?genre=Fantasy&sort=rating&q=Fantasy")
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.data)

    def test_paginated_shape(self):
        response = self.client.get("/api/books/")
        self.assertEqual(response.status_code, 200)
        for key in ("data", "page", "per_page", "total"):
            self.assertIn(key, response.data)

    def test_paginate_false_returns_flat_list(self):
        """Backward compat dla Vue — ?paginate=false zwraca array."""
        response = self.client.get("/api/books/?paginate=false")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
