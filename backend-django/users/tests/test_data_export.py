import json
import zipfile
from io import BytesIO

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from config.test_helpers import AuthTestHelper

User = get_user_model()

USER_PASSWORD = "password123"


class DataExportTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()

    def test_export_returns_200_with_zip(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post("/api/users/me/export/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp["Content-Type"], "application/zip")
        self.assertIn("attachment; filename=", resp["Content-Disposition"])

    def test_export_contains_only_user_and_readme(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post("/api/users/me/export/")
        zf = zipfile.ZipFile(BytesIO(resp.content))
        self.assertEqual(sorted(zf.namelist()), ["README.txt", "user.json"])

    def test_export_user_json_contains_handle(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post("/api/users/me/export/")
        zf = zipfile.ZipFile(BytesIO(resp.content))
        user_data = json.loads(zf.read("user.json"))
        self.assertEqual(user_data["handle"], "testuser")
        self.assertEqual(user_data["email"], "user@test.com")

    def test_export_unauthenticated_returns_401(self):
        resp = self.client.post("/api/users/me/export/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
