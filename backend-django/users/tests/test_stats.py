from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

from books.models import Book
from ratings.models import Rating
from shelf.models import ShelfEntry
from users.stats import build_user_stats

User = get_user_model()


class BuildUserStatsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="s@test.com", handle="stan", password="password123"
        )
        cls.b1 = Book.objects.create(title="B1", slug="b1", page_count=100)
        cls.b2 = Book.objects.create(title="B2", slug="b2", page_count=200)
        cls.b3 = Book.objects.create(title="B3", slug="b3", page_count=None)

        # Two READ (with finish dates), one READING, one WANT_TO_READ.
        ShelfEntry.objects.create(
            user=cls.user, book=cls.b1, status="READ",
            finish_date=date(2025, 3, 1),
        )
        ShelfEntry.objects.create(
            user=cls.user, book=cls.b2, status="READ",
            finish_date=date(2026, 1, 10),
        )
        ShelfEntry.objects.create(user=cls.user, book=cls.b3, status="READING")

        # Ratings: 5, 3.
        Rating.objects.create(user=cls.user, book=cls.b1, rating=5)
        Rating.objects.create(user=cls.user, book=cls.b2, rating=3)

    def test_status_counts(self):
        stats = build_user_stats(self.user)
        self.assertEqual(
            stats["status_counts"],
            {"want_to_read": 0, "reading": 1, "read": 2},
        )

    def test_totals(self):
        stats = build_user_stats(self.user)
        self.assertEqual(stats["totals"]["total_books"], 3)
        # pages_read = sum of READ books with page_count (100 + 200).
        self.assertEqual(stats["totals"]["pages_read"], 300)
        self.assertEqual(stats["totals"]["avg_rating_given"], 4.0)

    def test_books_per_year(self):
        stats = build_user_stats(self.user)
        self.assertEqual(
            stats["books_per_year"],
            [{"year": 2025, "count": 1}, {"year": 2026, "count": 1}],
        )

    def test_rating_distribution_zero_filled(self):
        stats = build_user_stats(self.user)
        self.assertEqual(
            stats["rating_distribution"],
            [
                {"rating": 1, "count": 0},
                {"rating": 2, "count": 0},
                {"rating": 3, "count": 1},
                {"rating": 4, "count": 0},
                {"rating": 5, "count": 1},
            ],
        )

    def test_time_on_shelf_days(self):
        # Both READ entries were created today (auto_now_add), finished in the
        # past relative to nothing — created_at is "now", finish_date is fixed.
        # So delta = finish_date - today (can be negative); assert it is a float.
        stats = build_user_stats(self.user)
        self.assertIsInstance(stats["time_on_shelf_days"], float)

    def test_empty_user(self):
        empty = User.objects.create_user(
            email="e@test.com", handle="empty", password="password123"
        )
        stats = build_user_stats(empty)
        self.assertEqual(
            stats["status_counts"], {"want_to_read": 0, "reading": 0, "read": 0}
        )
        self.assertEqual(stats["totals"]["total_books"], 0)
        self.assertEqual(stats["totals"]["pages_read"], 0)
        self.assertIsNone(stats["totals"]["avg_rating_given"])
        self.assertEqual(stats["books_per_year"], [])
        self.assertEqual(
            stats["rating_distribution"],
            [{"rating": r, "count": 0} for r in range(1, 6)],
        )
        self.assertIsNone(stats["time_on_shelf_days"])

    def test_only_own_data(self):
        other = User.objects.create_user(
            email="o@test.com", handle="otto", password="password123"
        )
        ShelfEntry.objects.create(user=other, book=self.b1, status="READ")
        Rating.objects.create(user=other, book=self.b1, rating=1)
        stats = build_user_stats(self.user)
        # Unchanged by other user's data.
        self.assertEqual(stats["status_counts"]["read"], 2)
        self.assertEqual(stats["totals"]["avg_rating_given"], 4.0)


from rest_framework import status as http_status
from rest_framework.test import APITestCase

STATS_URL = "/api/users/me/stats/"


class MyStatsEndpointTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="me@test.com", handle="mona", password="password123"
        )
        book = Book.objects.create(title="X", slug="x", page_count=120)
        ShelfEntry.objects.create(
            user=cls.user, book=book, status="READ", finish_date=date(2025, 6, 1)
        )
        Rating.objects.create(user=cls.user, book=book, rating=4)

    def test_requires_auth(self):
        resp = self.client.get(STATS_URL)
        self.assertEqual(resp.status_code, http_status.HTTP_401_UNAUTHORIZED)

    def test_returns_stats_shape(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(STATS_URL)
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        self.assertEqual(
            set(resp.data.keys()),
            {
                "status_counts",
                "totals",
                "books_per_year",
                "rating_distribution",
                "time_on_shelf_days",
            },
        )
        self.assertEqual(resp.data["status_counts"]["read"], 1)
        self.assertEqual(resp.data["totals"]["pages_read"], 120)
        self.assertEqual(resp.data["books_per_year"], [{"year": 2025, "count": 1}])
        self.assertEqual(len(resp.data["rating_distribution"]), 5)
