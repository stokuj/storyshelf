from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from config.test_helpers import AuthTestHelper
from users.serializers import RegisterSerializer

User = get_user_model()


class UserProfileTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()

    def setUp(self):
        self.target = User.objects.create_user(
            email="target@test.com",
            handle="targetuser",
            password="pw",
            bio="Hello world",
            profile_public=True,
        )
        self.url = f"/api/u/{self.target.handle}/"

    def test_get_public_profile_returns_200(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["handle"], "targetuser")
        self.assertEqual(resp.data["bio"], "Hello world")

    def test_get_nonexistent_user_returns_404(self):
        resp = self.client.get("/api/u/nonexistent/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_private_profile_returns_404_for_others(self):
        self.target.profile_public = False
        self.target.save()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_private_profile_returns_200_for_owner(self):
        self.target.profile_public = False
        self.target.save()
        self.client.force_authenticate(user=self.target)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class UserSettingsTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()

    def test_get_own_settings_returns_200(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/users/me/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["handle"], "testuser")
        self.assertIn("email", resp.data)
        self.assertIn("profile_public", resp.data)

    def test_get_settings_unauthenticated_returns_401(self):
        resp = self.client.get("/api/users/me/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_settings_empty_body_returns_200_noop(self):
        # Regression: empty PATCH must not raise KeyError -> 500.
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch("/api/users/me/settings/", {})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("profile_public", resp.data)

    def test_patch_settings_toggles_profile_public(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch("/api/users/me/settings/", {"profile_public": True})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["profile_public"])

    def test_register_serializer_rejects_weak_password(self):
        # Regression: registration must run Django password validators.
        # "abc123" fails both the field's min_length=8 and Django's
        # MinimumLengthValidator (8); the latter only runs via validate_password.
        serializer = RegisterSerializer(
            data={"email": "weak@test.com", "handle": "weakpwuser", "password": "abc123"}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_patch_settings_updates_bio(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch("/api/users/me/", {"bio": "New bio"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["bio"], "New bio")
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, "New bio")


class UserSettingsResponseStructureTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()

    def test_response_uses_snake_case_keys(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/users/me/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("profile_public", resp.data)
        self.assertIn("avatar_url", resp.data)
        self.assertIn("member_since", resp.data)


class RemovedEndpointsTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()

    def test_user_list_returns_404(self):
        resp = self.client.get("/api/users/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_data_export_returns_404(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get("/api/users/me/export/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
