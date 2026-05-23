from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book
from config.test_helpers import AuthTestHelper
from reviews.models import Review
from users.models import User


class ReviewEdgeCaseTest(AuthTestHelper, APITestCase):
    """Edge cases guarding against duplicate reviews, invalid ratings and permission leaks."""

    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(title="Review Book", isbn="r001", page_count=100, year=2023)

    def test_cannot_review_same_book_twice(self):
        Review.objects.create(user=self.user, book=self.book, rating=4, content="Nice")
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            "/api/reviews/",
            {"rating": 5, "content": "Even better", "bookId": self.book.id},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", resp.data)

    def test_rating_zero_returns_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            "/api/reviews/",
            {"rating": 0, "content": "Too low", "bookId": self.book.id},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rating_six_returns_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            "/api/reviews/",
            {"rating": 6, "content": "Too high", "bookId": self.book.id},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_edit_other_users_review(self):
        other = User.objects.create_user(
            email="other@test.com", handle="otheruser", password="password123"
        )
        review = Review.objects.create(user=other, book=self.book, rating=3, content="Meh")
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(
            f"/api/reviews/{review.id}/",
            {"content": "Hijacked"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_delete_other_users_review(self):
        other = User.objects.create_user(
            email="other2@test.com", handle="other2", password="password123"
        )
        review = Review.objects.create(user=other, book=self.book, rating=3, content="Meh")
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete(f"/api/reviews/{review.id}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_nonexistent_book_returns_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            "/api/reviews/",
            {"rating": 4, "content": "Great", "bookId": 99999},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("bookId", resp.data)

    def test_book_avg_rating_updated_on_delete(self):
        Review.objects.create(user=self.user, book=self.book, rating=4, content="Good")
        self.book.refresh_from_db()
        self.assertEqual(self.book.avg_rating, 4.0)
        self.client.force_authenticate(user=self.user)
        review = Review.objects.get(user=self.user, book=self.book)
        resp = self.client.delete(f"/api/reviews/{review.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.book.refresh_from_db()
        self.assertEqual(self.book.avg_rating, 0.0)
        self.assertEqual(self.book.ratings_count, 0)
