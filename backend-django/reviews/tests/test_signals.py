from django.test import TestCase

from books.models import Book
from config.test_helpers import AuthTestHelper
from reviews.models import Review
from users.models import User


class AvgRatingSignalTest(AuthTestHelper, TestCase):
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
