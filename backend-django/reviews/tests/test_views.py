from rest_framework import status
from rest_framework.test import APITestCase

from config.test_helpers import AuthTestHelper
from books.models import Book
from reviews.models import Review
from users.models import User


class ReviewListTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(title="Review Book", isbn="r001", page_count=100, year=2023)

    def test_get_reviews_empty_returns_200(self):
        resp = self.client.get("/api/reviews/?book_id=" + str(self.book.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    def test_get_reviews_with_data_returns_200(self):
        Review.objects.create(user=self.user, book=self.book, rating=4, content="Good book")
        resp = self.client.get("/api/reviews/?book_id=" + str(self.book.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["rating"], 4)
        self.assertEqual(resp.data[0]["username"], "testuser")

    def test_get_reviews_without_filter_returns_all(self):
        book2 = Book.objects.create(title="Other", isbn="r004", page_count=100, year=2023)
        Review.objects.create(user=self.user, book=self.book, rating=3, content="A")
        Review.objects.create(user=self.user, book=book2, rating=5, content="B")
        resp = self.client.get("/api/reviews/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 2)


class ReviewCreateTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(title="Review Book", isbn="r001", page_count=100, year=2023)

    def test_post_create_review_returns_201(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            "/api/reviews/",
            {
                "bookId": self.book.id,
                "rating": 5,
                "content": "Excellent!",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.filter(book=self.book, user=self.user).count(), 1)

    def test_post_create_review_unauthenticated_returns_401(self):
        resp = self.client.post(
            "/api/reviews/",
            {
                "bookId": self.book.id,
                "rating": 3,
                "content": "Test",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_create_review_duplicate_returns_400(self):
        Review.objects.create(user=self.user, book=self.book, rating=3, content="First")
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            "/api/reviews/",
            {
                "bookId": self.book.id,
                "rating": 4,
                "content": "Second?",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_create_review_invalid_rating_returns_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            "/api/reviews/",
            {
                "bookId": self.book.id,
                "rating": 6,
                "content": "Too high",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_create_review_missing_content_returns_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            "/api/reviews/",
            {
                "bookId": self.book.id,
                "rating": 3,
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_create_review_missing_rating_returns_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            "/api/reviews/",
            {
                "bookId": self.book.id,
                "content": "No rating",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_review_nonexistent_book_returns_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            "/api/reviews/",
            {"bookId": 99999, "rating": 3, "content": "Ghost book"},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class ReviewRetrieveTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(
            title="Struct Review", isbn="r003", page_count=100, year=2023
        )

    def test_review_response_has_camelcase_keys(self):
        review = Review.objects.create(user=self.user, book=self.book, rating=5, content="Super")
        resp = self.client.get(f"/api/reviews/{review.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.data
        self.assertIn("createdAt", data)
        self.assertIn("bookTitle", data)
        self.assertIn("bookId", data)
        self.assertIn("username", data)

    def test_get_nonexistent_review_returns_404(self):
        resp = self.client.get("/api/reviews/99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class ReviewUpdateTest(AuthTestHelper, APITestCase):
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

    def test_update_own_review_returns_200(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(f"/api/reviews/{self.review.id}/", {"content": "Updated!"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.review.refresh_from_db()
        self.assertEqual(self.review.content, "Updated!")

    def test_update_other_users_review_returns_403(self):
        other = User.objects.create_user(
            email="other@test.com", username="otheruser", password="password123"
        )
        other_review = Review.objects.create(user=other, book=self.book, rating=3, content="Other")
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(f"/api/reviews/{other_review.id}/", {"content": "Nope"})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_review_unauthenticated_returns_401(self):
        resp = self.client.patch(f"/api/reviews/{self.review.id}/", {"content": "No auth"})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


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

    def test_delete_own_review_returns_204(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete(f"/api/reviews/{self.review.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.filter(id=self.review.id).exists())

    def test_delete_other_users_review_returns_403(self):
        other = User.objects.create_user(
            email="other@test.com", username="otheruser", password="password123"
        )
        other_review = Review.objects.create(user=other, book=self.book, rating=3, content="Other")
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete(f"/api/reviews/{other_review.id}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_review_unauthenticated_returns_401(self):
        resp = self.client.delete(f"/api/reviews/{self.review.id}/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_nonexistent_review_returns_404(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete("/api/reviews/99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
