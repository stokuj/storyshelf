from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book
from config.test_helpers import AuthTestHelper
from shelf.models import ShelfEntry


class ShelfEdgeCaseTest(AuthTestHelper, APITestCase):
    """Edge cases for shelf: idempotence, invalid status, rating bounds."""

    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(title="Edge Book", isbn="e001", page_count=100, year=2023)

    def test_post_is_idempotent_no_duplicate(self):
        self.client.force_authenticate(user=self.user)
        resp1 = self.client.post(f"/api/shelf/{self.book.id}/", {"status": "WANT_TO_READ"})
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)
        resp2 = self.client.post(f"/api/shelf/{self.book.id}/", {"status": "WANT_TO_READ"})
        self.assertEqual(resp2.status_code, status.HTTP_201_CREATED)
        count = ShelfEntry.objects.filter(user=self.user, book=self.book).count()
        self.assertEqual(count, 1)

    def test_post_invalid_status_returns_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(f"/api/shelf/{self.book.id}/", {"status": "INVALID"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_invalid_status_returns_400(self):
        ShelfEntry.objects.create(user=self.user, book=self.book, status="WANT_TO_READ")
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(
            f"/api/shelf/{self.book.id}/",
            {"status": "NOTASTATUS"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_missing_status_returns_400(self):
        ShelfEntry.objects.create(user=self.user, book=self.book, status="WANT_TO_READ")
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(f"/api/shelf/{self.book.id}/", {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_personal_rating_out_of_bounds_ignored(self):
        entry = ShelfEntry.objects.create(
            user=self.user, book=self.book, status="READ", personal_rating=3
        )
        entry.personal_rating = 0
        entry.save()
        entry.refresh_from_db()
        # Django validators only run on full_clean; direct save bypasses them.
        # This documents the behaviour: model allows 0 if not validated.
        self.assertEqual(entry.personal_rating, 0)

    def test_create_then_get_then_delete_flow(self):
        self.client.force_authenticate(user=self.user)
        # create
        resp = self.client.post(f"/api/shelf/{self.book.id}/", {"status": "READING"})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        # get
        resp = self.client.get(f"/api/shelf/{self.book.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # delete
        resp = self.client.delete(f"/api/shelf/{self.book.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        # get after delete
        resp = self.client.get(f"/api/shelf/{self.book.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
