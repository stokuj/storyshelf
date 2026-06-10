from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book
from ratings.models import Rating
from reviews.models import Review, ReviewLike

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

    def test_put_without_book_slug_returns_400(self):
        self.client.force_authenticate(self.user)
        resp = self.client.put(URL, {"body": "x"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("book_slug", resp.data)

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


class ReviewLikeAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(
            email="auth@test.com", handle="author", password="password123"
        )
        cls.liker = User.objects.create_user(
            email="lk@test.com", handle="lk", password="password123"
        )
        cls.book = Book.objects.create(title="B", slug="b")
        cls.review = Review.objects.create(user=cls.author, book=cls.book, body="hello")

    def _url(self):
        return f"/api/reviews/{self.review.id}/like/"

    def test_post_like_returns_count_and_flag(self):
        self.client.force_authenticate(self.liker)
        resp = self.client.post(self._url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, {"likes_count": 1, "is_liked": True})

    def test_post_like_is_idempotent(self):
        self.client.force_authenticate(self.liker)
        self.client.post(self._url())
        resp = self.client.post(self._url())
        self.assertEqual(resp.data["likes_count"], 1)

    def test_delete_unlike(self):
        self.client.force_authenticate(self.liker)
        self.client.post(self._url())
        resp = self.client.delete(self._url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, {"likes_count": 0, "is_liked": False})

    def test_delete_when_not_liked_is_idempotent(self):
        self.client.force_authenticate(self.liker)
        resp = self.client.delete(self._url())
        self.assertEqual(resp.data, {"likes_count": 0, "is_liked": False})

    def test_like_requires_auth(self):
        resp = self.client.post(self._url())
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_like_unknown_review_404(self):
        self.client.force_authenticate(self.liker)
        resp = self.client.post("/api/reviews/99999/like/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_includes_likes_count_and_is_liked(self):
        ReviewLike.objects.create(user=self.liker, review=self.review)
        self.client.force_authenticate(self.liker)
        resp = self.client.get("/api/reviews/?book_slug=b")
        row = resp.data["data"][0]
        self.assertEqual(row["likes_count"], 1)
        self.assertTrue(row["is_liked"])

    def test_list_anon_is_liked_false(self):
        ReviewLike.objects.create(user=self.liker, review=self.review)
        resp = self.client.get("/api/reviews/?book_slug=b")
        row = resp.data["data"][0]
        self.assertEqual(row["likes_count"], 1)
        self.assertFalse(row["is_liked"])


class PublicUserReviewsTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.pub = User.objects.create_user(
            email="pub@test.com", handle="pub", password="password123", profile_public=True
        )
        cls.priv = User.objects.create_user(
            email="priv@test.com", handle="priv", password="password123", profile_public=False
        )
        cls.book = Book.objects.create(title="B", slug="b")
        Review.objects.create(user=cls.pub, book=cls.book, body="public review")
        Review.objects.create(user=cls.priv, book=cls.book, body="private review")

    def test_public_profile_reviews_listed(self):
        resp = self.client.get("/api/u/pub/reviews/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["total"], 1)
        self.assertEqual(resp.data["data"][0]["body"], "public review")

    def test_private_profile_returns_404(self):
        resp = self.client.get("/api/u/priv/reviews/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_unknown_handle_returns_404(self):
        resp = self.client.get("/api/u/ghost/reviews/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
