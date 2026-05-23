from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book
from config.test_helpers import AuthTestHelper
from shelf.models import ShelfEntry
from users.models import User


class ShelfListTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(title="Shelf Book", isbn="s001", page_count=100, year=2023)

    def test_get_shelf_authenticated_returns_200(self):
        ShelfEntry.objects.create(user=self.user, book=self.book, status="READING")
        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/shelf/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["status"], "READING")

    def test_get_shelf_unauthenticated_returns_401(self):
        resp = self.client.get("/api/shelf/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_shelf_empty_returns_200(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/shelf/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    def test_shelf_entries_isolated_per_user(self):
        other = User.objects.create_user(
            email="other@test.com", handle="otheruser", password="password123"
        )
        ShelfEntry.objects.create(user=self.user, book=self.book, status="READ")
        ShelfEntry.objects.create(user=other, book=self.book, status="WANT_TO_READ")
        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/shelf/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["status"], "READ")


class ShelfEntryTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(title="Entry Book", isbn="s002", page_count=100, year=2023)

    def test_post_create_entry_returns_201(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(f"/api/shelf/{self.book.id}/", {"status": "WANT_TO_READ"})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["status"], "WANT_TO_READ")
        self.assertTrue(ShelfEntry.objects.filter(user=self.user, book=self.book).exists())

    def test_post_create_entry_default_status_returns_201(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(f"/api/shelf/{self.book.id}/", {})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["status"], "WANT_TO_READ")

    def test_post_create_entry_unauthenticated_returns_401(self):
        resp = self.client.post(f"/api/shelf/{self.book.id}/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_create_entry_nonexistent_book_returns_404(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post("/api/shelf/99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_entry_returns_200(self):
        ShelfEntry.objects.create(user=self.user, book=self.book, status="READING")
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(f"/api/shelf/{self.book.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["status"], "READING")

    def test_get_entry_not_found_returns_404(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(f"/api/shelf/{self.book.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_update_status_returns_200(self):
        ShelfEntry.objects.create(user=self.user, book=self.book, status="WANT_TO_READ")
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(f"/api/shelf/{self.book.id}/", {"status": "READ"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["status"], "READ")

    def test_patch_missing_status_returns_400(self):
        ShelfEntry.objects.create(user=self.user, book=self.book, status="WANT_TO_READ")
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(f"/api/shelf/{self.book.id}/", {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_entry_returns_204(self):
        ShelfEntry.objects.create(user=self.user, book=self.book, status="READ")
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete(f"/api/shelf/{self.book.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ShelfEntry.objects.filter(user=self.user, book=self.book).exists())

    def test_delete_entry_unauthenticated_returns_401(self):
        ShelfEntry.objects.create(user=self.user, book=self.book, status="READ")
        resp = self.client.delete(f"/api/shelf/{self.book.id}/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_access_other_user_entry(self):
        other = User.objects.create_user(
            email="other@test.com", handle="otheruser", password="password123"
        )
        ShelfEntry.objects.create(user=other, book=self.book, status="READ")
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(f"/api/shelf/{self.book.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class ShelfResponseStructureTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(title="Struct Book", isbn="s003", page_count=100, year=2023)

    def test_response_uses_camelcase_keys(self):
        ShelfEntry.objects.create(user=self.user, book=self.book, status="READING")
        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/shelf/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        entry = resp.data[0]
        self.assertIn("createdAt", entry)
        self.assertIn("book", entry)
        self.assertIn("id", entry["book"])
        self.assertIn("title", entry["book"])
        self.assertIn("author", entry["book"])


class ShelfEntryDateValidationTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(title="Date Book", year=2020, page_count=100)

    def test_finish_before_start_returns_400(self):
        self.client.force_authenticate(user=self.user)
        ShelfEntry.objects.filter(user=self.user, book=self.book).delete()
        self.client.post(f"/api/shelf/{self.book.id}/", {"status": "READING"})
        resp = self.client.patch(
            f"/api/shelf/{self.book.id}/",
            {"status": "READ", "start_date": "2024-06-01", "finish_date": "2024-05-01"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_finish_equals_start_is_valid(self):
        self.client.force_authenticate(user=self.user)
        ShelfEntry.objects.filter(user=self.user, book=self.book).delete()
        self.client.post(f"/api/shelf/{self.book.id}/", {"status": "READING"})
        resp = self.client.patch(
            f"/api/shelf/{self.book.id}/",
            {"status": "READ", "start_date": "2024-06-01", "finish_date": "2024-06-01"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
