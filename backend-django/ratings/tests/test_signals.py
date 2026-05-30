from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from books.models import Book
from ratings.models import Rating

User = get_user_model()


class AvgRatingSignalTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="a@test.com", handle="alice", password="password123"
        )
        cls.user2 = User.objects.create_user(
            email="b@test.com", handle="bob", password="password123"
        )
        cls.book = Book.objects.create(title="Signal Test", slug="signal-test")

    def test_avg_and_count_after_save(self):
        Rating.objects.create(user=self.user, book=self.book, rating=4)
        self.book.refresh_from_db()
        self.assertEqual(self.book.avg_rating, 4.0)
        self.assertEqual(self.book.ratings_count, 1)

        Rating.objects.create(user=self.user2, book=self.book, rating=2)
        self.book.refresh_from_db()
        self.assertEqual(self.book.avg_rating, 3.0)  # (4+2)/2
        self.assertEqual(self.book.ratings_count, 2)

    def test_avg_resets_to_zero_after_all_deleted(self):
        r = Rating.objects.create(user=self.user, book=self.book, rating=5)
        r.delete()
        self.book.refresh_from_db()
        self.assertEqual(self.book.avg_rating, 0.0)
        self.assertEqual(self.book.ratings_count, 0)
