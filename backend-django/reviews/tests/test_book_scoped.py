from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from reviews.models import Review
from users.models import User


class BookScopedReviewsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="reviewer@test.com", handle="reviewer", password="pass123"
        )
        self.book = Book.objects.create(title="Test Book")
        self.other_book = Book.objects.create(title="Other Book")
        Review.objects.create(book=self.book, user=self.user, rating=4, content="Great")
        Review.objects.create(book=self.other_book, user=self.user, rating=3, content="OK")

    def test_list_reviews_scoped_to_book_by_id(self):
        response = self.client.get(f"/api/books/{self.book.pk}/reviews/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("data", response.data)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["rating"], 4)

    def test_list_reviews_scoped_to_book_by_slug(self):
        response = self.client.get(f"/api/books/{self.book.slug}/reviews/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)

    def test_list_reviews_returns_paginated_shape(self):
        response = self.client.get(f"/api/books/{self.book.pk}/reviews/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for key in ("data", "page", "per_page", "total"):
            self.assertIn(key, response.data)

    def test_create_review_scoped_no_book_id_in_body(self):
        self.client.force_authenticate(user=self.user)
        new_book = Book.objects.create(title="Brand New Book")
        response = self.client.post(
            f"/api/books/{new_book.pk}/reviews/",
            {"rating": 5, "content": "Amazing"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.filter(book=new_book).count(), 1)

    def test_create_review_requires_authentication(self):
        new_book = Book.objects.create(title="Auth Test Book")
        response = self.client.post(
            f"/api/books/{new_book.pk}/reviews/",
            {"rating": 4, "content": "Test"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_review_404_for_nonexistent_book(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/books/99999/reviews/",
            {"rating": 3, "content": "Ghost"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
