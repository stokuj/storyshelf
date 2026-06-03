from datetime import date, timedelta

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book
from library.models import Author, Genre
from ratings.models import Rating
from shelf.models import ShelfEntry

User = get_user_model()

URL = "/api/shelf/entries/"


class ShelfEntryAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="a@test.com", handle="alice", password="password123"
        )
        cls.other = User.objects.create_user(
            email="b@test.com", handle="bob", password="password123"
        )
        cls.author = Author.objects.create(name="J.R.R. Tolkien")
        cls.genre = Genre.objects.create(name="Fantasy")
        cls.book = Book.objects.create(title="The Hobbit", slug="the-hobbit", page_count=310)
        cls.book.authors.add(cls.author)
        cls.book.genres.add(cls.genre)
        cls.book_no_pages = Book.objects.create(title="No Pages", slug="no-pages", page_count=None)
        cls.today = date.today()

    def _detail(self, pk):
        return f"{URL}{pk}/"

    # ── CRUD ──
    def test_create_defaults_to_want_to_read(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(URL, {"book_slug": "the-hobbit"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["status"], "WANT_TO_READ")
        self.assertEqual(resp.data["book"]["slug"], "the-hobbit")
        self.assertEqual(resp.data["book"]["authors"], ["J.R.R. Tolkien"])
        self.assertEqual(resp.data["book"]["genres"], ["Fantasy"])
        self.assertIsNone(resp.data["current_page"])
        self.assertIsNone(resp.data["user_rating"])

    def test_list_returns_plain_list(self):
        self.client.force_authenticate(self.user)
        ShelfEntry.objects.create(user=self.user, book=self.book)
        resp = self.client.get(URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsInstance(resp.data, list)
        self.assertEqual(len(resp.data), 1)

    def test_filter_by_book_slug(self):
        self.client.force_authenticate(self.user)
        ShelfEntry.objects.create(user=self.user, book=self.book)
        ShelfEntry.objects.create(user=self.user, book=self.book_no_pages)
        resp = self.client.get(URL, {"book_slug": "the-hobbit"})
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["book"]["slug"], "the-hobbit")

    def test_patch_status(self):
        self.client.force_authenticate(self.user)
        entry = ShelfEntry.objects.create(user=self.user, book=self.book)
        resp = self.client.patch(self._detail(entry.id), {"status": "READING"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["status"], "READING")

    def test_delete(self):
        self.client.force_authenticate(self.user)
        entry = ShelfEntry.objects.create(user=self.user, book=self.book)
        resp = self.client.delete(self._detail(entry.id))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ShelfEntry.objects.filter(id=entry.id).exists())

    # ── validation ──
    def test_duplicate_returns_400(self):
        self.client.force_authenticate(self.user)
        ShelfEntry.objects.create(user=self.user, book=self.book)
        resp = self.client.post(URL, {"book_slug": "the-hobbit"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_current_page_exceeds_page_count_returns_400(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            URL, {"book_slug": "the-hobbit", "current_page": 999}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_current_page_exceeds_page_count_returns_400(self):
        self.client.force_authenticate(self.user)
        entry = ShelfEntry.objects.create(user=self.user, book=self.book)
        resp = self.client.patch(
            self._detail(entry.id), {"current_page": 999}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_current_page_ok_when_page_count_null(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(URL, {"book_slug": "no-pages", "current_page": 500}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["current_page"], 500)

    def test_finish_before_start_returns_400(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            URL,
            {
                "book_slug": "the-hobbit",
                "start_date": str(self.today),
                "finish_date": str(self.today - timedelta(days=1)),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_book_slug_returns_400(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(URL, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # ── isolation ──
    def test_anonymous_returns_401(self):
        resp = self.client.get(URL)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_a_cannot_see_user_b_entries(self):
        ShelfEntry.objects.create(user=self.other, book=self.book)
        self.client.force_authenticate(self.user)
        resp = self.client.get(URL)
        self.assertEqual(len(resp.data), 0)

    def test_patch_other_users_entry_returns_404(self):
        entry = ShelfEntry.objects.create(user=self.other, book=self.book)
        self.client.force_authenticate(self.user)
        resp = self.client.patch(self._detail(entry.id), {"status": "READ"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_book_slug_returns_400(self):
        self.client.force_authenticate(self.user)
        entry = ShelfEntry.objects.create(user=self.user, book=self.book)
        resp = self.client.patch(self._detail(entry.id), {"book_slug": "no-pages"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        entry.refresh_from_db()
        self.assertEqual(entry.book, self.book)  # unchanged

    def test_delete_other_users_entry_returns_404(self):
        entry = ShelfEntry.objects.create(user=self.other, book=self.book)
        self.client.force_authenticate(self.user)
        resp = self.client.delete(self._detail(entry.id))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(ShelfEntry.objects.filter(id=entry.id).exists())  # not deleted

    # ── user_rating Subquery ──
    def test_user_rating_populated(self):
        Rating.objects.create(user=self.user, book=self.book, rating=4)
        self.client.force_authenticate(self.user)
        entry = ShelfEntry.objects.create(user=self.user, book=self.book)
        resp = self.client.get(self._detail(entry.id))
        self.assertEqual(resp.data["user_rating"], 4)

    def test_user_rating_null_when_no_rating(self):
        self.client.force_authenticate(self.user)
        entry = ShelfEntry.objects.create(user=self.user, book=self.book)
        resp = self.client.get(self._detail(entry.id))
        self.assertIsNone(resp.data["user_rating"])


class FinishDateAutoSetTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="fd@test.com", handle="finn", password="password123"
        )
        cls.book = Book.objects.create(title="Dune", slug="dune", page_count=412)
        cls.today = date.today()

    def _detail(self, pk):
        return f"{URL}{pk}/"

    def test_patch_to_read_sets_finish_date(self):
        self.client.force_authenticate(self.user)
        entry = ShelfEntry.objects.create(user=self.user, book=self.book)
        resp = self.client.patch(
            self._detail(entry.pk), {"status": "READ"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["finish_date"], self.today.isoformat())

    def test_create_as_read_sets_finish_date(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            URL, {"book_slug": "dune", "status": "READ"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["finish_date"], self.today.isoformat())

    def test_existing_finish_date_not_overwritten(self):
        self.client.force_authenticate(self.user)
        entry = ShelfEntry.objects.create(
            user=self.user, book=self.book, status="READ",
            finish_date=date(2020, 1, 1),
        )
        resp = self.client.patch(
            self._detail(entry.pk), {"current_page": 10}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["finish_date"], "2020-01-01")

    def test_explicit_finish_date_respected(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            URL,
            {"book_slug": "dune", "status": "READ", "finish_date": "2019-05-05"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["finish_date"], "2019-05-05")

    def test_non_read_status_does_not_set_finish_date(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            URL, {"book_slug": "dune", "status": "READING"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(resp.data["finish_date"])
