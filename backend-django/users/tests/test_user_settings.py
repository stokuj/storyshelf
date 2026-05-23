from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from config.test_helpers import AuthTestHelper

User = get_user_model()


class UserSettingsPatchTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()

    def test_patch_settings_sets_profile_private(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch("/api/users/me/settings/", {"profile_public": False})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["profile_public"])
        self.user.refresh_from_db()
        self.assertFalse(self.user.profile_public)

    def test_patch_settings_sets_profile_public(self):
        self.user.profile_public = False
        self.user.save()
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch("/api/users/me/settings/", {"profile_public": True})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["profile_public"])

    def test_patch_settings_unauthenticated_returns_401(self):
        resp = self.client.patch("/api/users/me/settings/", {"profile_public": False})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
