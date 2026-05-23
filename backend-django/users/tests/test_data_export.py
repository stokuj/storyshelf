import json
import zipfile
from io import BytesIO

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book
from config.test_helpers import AuthTestHelper
from reviews.models import Review
from shelf.models import ShelfEntry

User = get_user_model()

USER_PASSWORD = "password123"


class DataExportTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        # Add some data to the user
        cls.book = Book.objects.create(title="Test Book")
        ShelfEntry.objects.create(
            user=cls.user, book=cls.book, status=ShelfEntry.Status.READ,
            finish_date="2026-01-15",
        )
        Review.objects.create(
            user=cls.user, book=cls.book, rating=4, content="Great book!",
        )

    def test_export_returns_200_with_zip(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post("/api/users/me/export/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp["Content-Type"], "application/zip")
        self.assertIn("attachment; filename=", resp["Content-Disposition"])

    def test_export_contains_expected_json_files(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post("/api/users/me/export/")
        zf = zipfile.ZipFile(BytesIO(resp.content))
        names = zf.namelist()
        self.assertIn("user.json", names)
        self.assertIn("shelf_entries.json", names)
        self.assertIn("reviews.json", names)
        self.assertIn("follows.json", names)
        self.assertIn("README.txt", names)

    def test_export_user_json_contains_handle(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post("/api/users/me/export/")
        zf = zipfile.ZipFile(BytesIO(resp.content))
        user_data = json.loads(zf.read("user.json"))
        self.assertEqual(user_data["handle"], "testuser")
        self.assertEqual(user_data["email"], "user@test.com")

    def test_export_shelf_entries_contains_data(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post("/api/users/me/export/")
        zf = zipfile.ZipFile(BytesIO(resp.content))
        entries = json.loads(zf.read("shelf_entries.json"))
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["book_title"], "Test Book")

    def test_export_reviews_contains_data(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post("/api/users/me/export/")
        zf = zipfile.ZipFile(BytesIO(resp.content))
        reviews = json.loads(zf.read("reviews.json"))
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0]["rating"], 4)

    def test_export_follows_json_has_correct_structure(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post("/api/users/me/export/")
        zf = zipfile.ZipFile(BytesIO(resp.content))
        follows = json.loads(zf.read("follows.json"))
        self.assertIn("following", follows)
        self.assertIn("followers", follows)

    def test_export_unauthenticated_returns_401(self):
        resp = self.client.post("/api/users/me/export/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_export_empty_user_works(self):
        empty_user = User.objects.create_user(
            email="empty@test.com", handle="emptyuser", password="pw123456"
        )
        self.client.force_authenticate(user=empty_user)
        resp = self.client.post("/api/users/me/export/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        zf = zipfile.ZipFile(BytesIO(resp.content))
        entries = json.loads(zf.read("shelf_entries.json"))
        self.assertEqual(entries, [])
