from django.utils.timezone import now
from rest_framework.test import APITestCase

from books.models import Book
from ratings.models import Rating
from users.models import User, UserFollow


class FeedTieGroupTests(APITestCase):
    def test_large_same_timestamp_group_not_dropped(self):
        # A tie group larger than the per-source fetch window (PAGE_SIZE + 1 = 21)
        # must not be silently truncated by the strict `<` cursor.
        me = User.objects.create_user(email="me@e.test", handle="me", password="password123")
        author = User.objects.create_user(
            email="a@e.test", handle="auth", password="password123", profile_public=True
        )
        UserFollow.objects.create(follower=me, following=author)

        ts = now()
        for n in range(22):
            book = Book.objects.create(title=f"B{n}", slug=f"b{n}")
            Rating.objects.create(user=author, book=book, rating=4)
        # Force identical timestamps (bulk update bypasses auto_now).
        Rating.objects.filter(user=author).update(updated_at=ts)

        self.client.force_authenticate(me)
        res = self.client.get("/api/feed/")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data["results"]), 22)
        self.assertIsNone(res.data["next_before"])
