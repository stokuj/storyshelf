from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from books.models import Book
from reviews.models import Review

User = get_user_model()


class ReviewModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="a@test.com", handle="alice", password="password123"
        )
        cls.book = Book.objects.create(title="Book One", slug="book-one")

    def test_one_review_per_user_book(self):
        Review.objects.create(user=self.user, book=self.book, body="First")
        with self.assertRaises(IntegrityError):
            Review.objects.create(user=self.user, book=self.book, body="Second")
