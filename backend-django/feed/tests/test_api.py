from django.contrib.auth import get_user_model
from django.utils.timezone import now
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book
from ratings.models import Rating
from reviews.models import Review
from shelf.models import ShelfEntry
from users.models import UserFollow

User = get_user_model()
FEED_URL = "/api/feed/"


class FeedAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.me = User.objects.create_user(
            email="me@test.com", handle="me", password="password123"
        )
        cls.pub = User.objects.create_user(
            email="pub@test.com", handle="pub", password="password123", profile_public=True
        )
        cls.priv = User.objects.create_user(
            email="priv@test.com", handle="priv", password="password123", profile_public=False
        )
        cls.book = Book.objects.create(title="B", slug="b", cover_url="http://x/c.jpg")
        UserFollow.objects.create(follower=cls.me, following=cls.pub)
        UserFollow.objects.create(follower=cls.me, following=cls.priv)

    def test_requires_auth(self):
        resp = self.client.get(FEED_URL)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_feed_includes_followed_public_activity(self):
        Rating.objects.create(user=self.pub, book=self.book, rating=5)
        Review.objects.create(user=self.pub, book=self.book, body="great")
        self.client.force_authenticate(self.me)
        resp = self.client.get(FEED_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        types = {item["type"] for item in resp.data["results"]}
        self.assertEqual(types, {"rating", "review"})
        self.assertEqual(resp.data["results"][0]["actor"]["handle"], "pub")

    def test_finished_book_appears(self):
        ShelfEntry.objects.create(
            user=self.pub,
            book=self.book,
            status=ShelfEntry.Status.READ,
            finished_at=now(),
        )
        self.client.force_authenticate(self.me)
        resp = self.client.get(FEED_URL)
        self.assertEqual(resp.data["results"][0]["type"], "finished")

    def test_private_user_excluded(self):
        Rating.objects.create(user=self.priv, book=self.book, rating=4)
        self.client.force_authenticate(self.me)
        resp = self.client.get(FEED_URL)
        self.assertEqual(resp.data["results"], [])

    def test_own_activity_excluded(self):
        Rating.objects.create(user=self.me, book=self.book, rating=3)
        self.client.force_authenticate(self.me)
        resp = self.client.get(FEED_URL)
        self.assertEqual(resp.data["results"], [])

    def test_pagination_cursor(self):
        for i in range(25):
            b = Book.objects.create(title=f"B{i}", slug=f"b{i}")
            Rating.objects.create(user=self.pub, book=b, rating=5)
        self.client.force_authenticate(self.me)
        resp = self.client.get(FEED_URL)
        self.assertEqual(len(resp.data["results"]), 20)
        self.assertIsNotNone(resp.data["next_before"])
        resp2 = self.client.get(FEED_URL, {"before": resp.data["next_before"]})
        self.assertEqual(len(resp2.data["results"]), 5)
        self.assertIsNone(resp2.data["next_before"])
