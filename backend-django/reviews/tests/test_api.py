from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book
from ratings.models import Rating
from reviews.models import Review

User = get_user_model()

URL = "/api/reviews/"
ME_URL = "/api/reviews/me/"


class ReviewAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="a@test.com", handle="alice", display_name="Alice", password="password123"
        )
        cls.user_b = User.objects.create_user(
            email="b@test.com", handle="bob", display_name="Bob", password="password123"
        )
        cls.book = Book.objects.create(title="Book One", slug="book-one")
        cls.book2 = Book.objects.create(title="Book Two", slug="book-two")

    # ── upsert ──
    def test_put_create_returns_201(self):
        self.client.force_authenticate(self.user)
        resp = self.client.put(URL, {"book_slug": "book-one", "body": "Great read"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["body"], "Great read")
        self.assertEqual(resp.data["author"]["handle"], "alice")

    def test_put_update_returns_200(self):
        self.client.force_authenticate(self.user)
        self.client.put(URL, {"book_slug": "book-one", "body": "v1"}, format="json")
        resp = self.client.put(URL, {"book_slug": "book-one", "body": "v2"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["body"], "v2")
        self.assertEqual(Review.objects.filter(user=self.user, book=self.book).count(), 1)

    def test_put_unknown_book_returns_404(self):
        self.client.force_authenticate(self.user)
        resp = self.client.put(URL, {"book_slug": "nope", "body": "x"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_empty_body_returns_400(self):
        self.client.force_authenticate(self.user)
        resp = self.client.put(URL, {"book_slug": "book-one", "body": "   "}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_anonymous_put_returns_401(self):
        resp = self.client.put(URL, {"book_slug": "book-one", "body": "x"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── public list ──
    def test_list_is_public_and_paginated(self):
        Review.objects.create(user=self.user, book=self.book, body="from alice")
        Review.objects.create(user=self.user_b, book=self.book, body="from bob")
        resp = self.client.get(URL, {"book_slug": "book-one"})  # anonymous
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("data", resp.data)
        self.assertEqual(resp.data["total"], 2)

    def test_list_filter_by_book_slug(self):
        Review.objects.create(user=self.user, book=self.book, body="one")
        Review.objects.create(user=self.user, book=self.book2, body="two")
        resp = self.client.get(URL, {"book_slug": "book-two"})
        self.assertEqual(resp.data["total"], 1)
        self.assertEqual(resp.data["data"][0]["body"], "two")

    def test_list_includes_author_rating_when_present(self):
        Review.objects.create(user=self.user, book=self.book, body="rated")
        Rating.objects.create(user=self.user, book=self.book, rating=4)
        resp = self.client.get(URL, {"book_slug": "book-one"})
        self.assertEqual(resp.data["data"][0]["author_rating"], 4)

    def test_list_author_rating_null_when_absent(self):
        Review.objects.create(user=self.user, book=self.book, body="unrated")
        resp = self.client.get(URL, {"book_slug": "book-one"})
        self.assertIsNone(resp.data["data"][0]["author_rating"])

    # ── me ──
    def test_me_returns_own_review(self):
        self.client.force_authenticate(self.user)
        self.client.put(URL, {"book_slug": "book-one", "body": "mine"}, format="json")
        resp = self.client.get(ME_URL, {"book_slug": "book-one"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["body"], "mine")

    def test_me_returns_404_when_none(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(ME_URL, {"book_slug": "book-one"})
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_me_requires_auth(self):
        resp = self.client.get(ME_URL, {"book_slug": "book-one"})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── delete ──
    def test_delete_own_returns_204(self):
        self.client.force_authenticate(self.user)
        created = self.client.put(URL, {"book_slug": "book-one", "body": "x"}, format="json")
        resp = self.client.delete(f"{URL}{created.data['id']}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_cannot_delete_others_review(self):
        review = Review.objects.create(user=self.user_b, book=self.book, body="bob's")
        self.client.force_authenticate(self.user)
        resp = self.client.delete(f"{URL}{review.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Review.objects.filter(id=review.id).exists())

    def test_put_response_includes_author_rating(self):
        self.client.force_authenticate(self.user)
        Rating.objects.create(user=self.user, book=self.book, rating=5)
        resp = self.client.put(
            URL, {"book_slug": "book-one", "body": "rated then reviewed"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["author_rating"], 5)

    def test_me_includes_author_rating(self):
        self.client.force_authenticate(self.user)
        Rating.objects.create(user=self.user, book=self.book, rating=2)
        self.client.put(URL, {"book_slug": "book-one", "body": "mine"}, format="json")
        resp = self.client.get(ME_URL, {"book_slug": "book-one"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["author_rating"], 2)
