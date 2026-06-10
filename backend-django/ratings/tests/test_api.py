from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book
from ratings.models import Rating

User = get_user_model()

URL = "/api/ratings/"


class RatingAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="a@test.com", handle="alice", password="password123"
        )
        cls.user_b = User.objects.create_user(
            email="b@test.com", handle="bob", password="password123"
        )
        cls.book = Book.objects.create(title="Book One", slug="book-one")
        cls.book2 = Book.objects.create(title="Book Two", slug="book-two")

    # ── upsert ──
    def test_put_create_returns_201(self):
        self.client.force_authenticate(self.user)
        resp = self.client.put(URL, {"book_slug": "book-one", "rating": 4}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["book_slug"], "book-one")
        self.assertEqual(resp.data["rating"], 4)

    def test_put_update_returns_200(self):
        self.client.force_authenticate(self.user)
        self.client.put(URL, {"book_slug": "book-one", "rating": 3}, format="json")
        resp = self.client.put(URL, {"book_slug": "book-one", "rating": 5}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["rating"], 5)
        self.assertEqual(Rating.objects.filter(user=self.user, book=self.book).count(), 1)

    # ── list (user-scoped, not paginated) ──
    def test_list_returns_plain_list_of_own_ratings(self):
        self.client.force_authenticate(self.user)
        self.client.put(URL, {"book_slug": "book-one", "rating": 3}, format="json")
        self.client.put(URL, {"book_slug": "book-two", "rating": 2}, format="json")
        resp = self.client.get(URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsInstance(resp.data, list)  # pagination_class = None
        self.assertEqual(len(resp.data), 2)

    def test_list_filter_by_book_slug(self):
        self.client.force_authenticate(self.user)
        self.client.put(URL, {"book_slug": "book-one", "rating": 3}, format="json")
        resp = self.client.get(URL, {"book_slug": "book-one"})
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["book_slug"], "book-one")

    # ── delete ──
    def test_delete_returns_204(self):
        self.client.force_authenticate(self.user)
        created = self.client.put(URL, {"book_slug": "book-one", "rating": 3}, format="json")
        resp = self.client.delete(f"{URL}{created.data['id']}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    # ── validation ──
    def test_rating_out_of_range_returns_400(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(
            self.client.put(URL, {"book_slug": "book-one", "rating": 0}, format="json").status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            self.client.put(URL, {"book_slug": "book-one", "rating": 6}, format="json").status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_put_unknown_book_returns_404(self):
        self.client.force_authenticate(self.user)
        resp = self.client.put(URL, {"book_slug": "nope", "rating": 3}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_without_book_slug_returns_400(self):
        self.client.force_authenticate(self.user)
        resp = self.client.put(URL, {"rating": 4}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("book_slug", resp.data)

    # ── permissions / isolation ──
    def test_anonymous_put_returns_401(self):
        resp = self.client.put(URL, {"book_slug": "book-one", "rating": 3}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_a_cannot_see_user_b_ratings(self):
        self.client.force_authenticate(self.user_b)
        self.client.put(URL, {"book_slug": "book-one", "rating": 5}, format="json")
        self.client.force_authenticate(self.user)
        resp = self.client.get(URL)
        self.assertEqual(len(resp.data), 0)

    def test_delete_other_users_rating_returns_404(self):
        rating = Rating.objects.create(user=self.user_b, book=self.book, rating=5)
        self.client.force_authenticate(self.user)
        resp = self.client.delete(f"{URL}{rating.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Rating.objects.filter(id=rating.id).exists())
