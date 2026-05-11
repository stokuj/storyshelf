from rest_framework import status
from rest_framework.test import APITestCase

from config.test_helpers import AuthTestHelper
from books.models import Book
from reviews.models import Review


class BookReviewListCreateTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(
            title="Review Book", isbn="r001", page_count=100, year=2023
        )

    def test_get_reviews_empty_returns_200(self):
        resp = self.client.get(f"/api/books/{self.book.id}/reviews/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    def test_get_reviews_with_data_returns_200(self):
        Review.objects.create(
            user=self.user, book=self.book, rating=4, content="Good book"
        )
        resp = self.client.get(f"/api/books/{self.book.id}/reviews/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["rating"], 4)
        self.assertEqual(resp.data[0]["username"], "testuser")

    def test_post_create_review_returns_201(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            f"/api/books/{self.book.id}/reviews/",
            {
                "rating": 5,
                "content": "Excellent!",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Review.objects.filter(book=self.book, user=self.user).count(), 1
        )

    def test_post_create_review_unauthenticated_returns_401(self):
        resp = self.client.post(
            f"/api/books/{self.book.id}/reviews/",
            {
                "rating": 3,
                "content": "Test",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_create_review_duplicate_returns_400(self):
        Review.objects.create(user=self.user, book=self.book, rating=3, content="First")
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            f"/api/books/{self.book.id}/reviews/",
            {
                "rating": 4,
                "content": "Second?",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_create_review_invalid_rating_returns_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            f"/api/books/{self.book.id}/reviews/",
            {
                "rating": 6,
                "content": "Too high",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_create_review_missing_content_returns_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            f"/api/books/{self.book.id}/reviews/",
            {
                "rating": 3,
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_create_review_missing_rating_returns_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            f"/api/books/{self.book.id}/reviews/",
            {
                "content": "No rating",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class ReviewDeleteTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(
            title="Del Review Book", isbn="r002", page_count=100, year=2023
        )

    def setUp(self):
        self.review = Review.objects.create(
            user=self.user, book=self.book, rating=4, content="Nice"
        )

    def test_delete_review_as_moderator_returns_204(self):
        self.client.force_authenticate(user=self.moderator)
        resp = self.client.delete(f"/api/reviews/{self.review.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.filter(id=self.review.id).exists())

    def test_delete_review_as_admin_returns_204(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.delete(f"/api/reviews/{self.review.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_review_as_regular_user_returns_403(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete(f"/api/reviews/{self.review.id}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_review_unauthenticated_returns_401(self):
        resp = self.client.delete(f"/api/reviews/{self.review.id}/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_nonexistent_review_returns_404(self):
        self.client.force_authenticate(user=self.moderator)
        resp = self.client.delete("/api/reviews/99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class ReviewResponseStructureTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(
            title="Struct Review", isbn="r003", page_count=100, year=2023
        )

    def test_review_response_has_camelcase_keys(self):
        Review.objects.create(user=self.user, book=self.book, rating=5, content="Super")
        resp = self.client.get(f"/api/books/{self.book.id}/reviews/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        review = resp.data[0]
        self.assertIn("createdAt", review)
        self.assertIn("bookTitle", review)
        self.assertIn("bookId", review)
        self.assertIn("username", review)
