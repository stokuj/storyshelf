from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from config.test_helpers import AuthTestHelper

User = get_user_model()

USER_PASSWORD = "password123"


class UserMeModelTest(APITestCase):
    def test_user_has_handle_field(self):
        u = User.objects.create_user(email="a@test.com", handle="alice", password="pw123456")
        self.assertEqual(u.handle, "alice")

    def test_user_has_display_name_field(self):
        u = User.objects.create_user(email="b@test.com", handle="bob", password="pw123456")
        self.assertEqual(u.display_name, "")

    def test_user_has_avatar_imagefield(self):
        u = User.objects.create_user(email="c@test.com", handle="carol", password="pw123456")
        self.assertIsNone(u.avatar.name)

    def test_user_has_no_username_field(self):
        u = User.objects.create_user(email="d@test.com", handle="dave", password="pw123456")
        self.assertFalse(hasattr(u, "username"))


class UserMeGetTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()

    def test_get_me_returns_200_with_snake_case_fields(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/users/me/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("handle", resp.data)
        self.assertIn("display_name", resp.data)
        self.assertIn("email", resp.data)
        self.assertIn("settings", resp.data)
        self.assertIn("profile_public", resp.data["settings"])
        self.assertNotIn("username", resp.data)
        self.assertNotIn("profilePublic", resp.data)

    def test_get_me_unauthenticated_returns_401(self):
        resp = self.client.get("/api/users/me/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class UserMePatchTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()

    def test_patch_bio_updates(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch("/api/users/me/", {"bio": "New bio"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, "New bio")

    def test_patch_display_name_updates(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch("/api/users/me/", {"display_name": "Test User"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.display_name, "Test User")

    def test_patch_handle_conflict_returns_400(self):
        other = User.objects.create_user(
            email="other@test.com", handle="otheruser", password="pw123456"
        )
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch("/api/users/me/", {"handle": "otheruser"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_handle_invalid_format_returns_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch("/api/users/me/", {"handle": "Has Spaces"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_email_ignored(self):
        self.client.force_authenticate(user=self.user)
        original_email = self.user.email
        resp = self.client.patch("/api/users/me/", {"email": "hacker@evil.com"})
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, original_email)


class AccountDeleteTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.user_id = cls.user.pk

    def setUp(self):
        self.user = User.objects.get(pk=self.user_id)

    def test_delete_with_correct_password_returns_204(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete("/api/users/me/", {"current_password": USER_PASSWORD})
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())

    def test_delete_with_wrong_password_returns_403(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete("/api/users/me/", {"current_password": "wrongpassword"})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(User.objects.filter(pk=self.user_id).exists())

    def test_delete_unauthenticated_returns_401(self):
        resp = self.client.delete("/api/users/me/", {"current_password": USER_PASSWORD})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_clears_jwt_cookies(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete("/api/users/me/", {"current_password": USER_PASSWORD})
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIn("access_token", resp.cookies)
        self.assertEqual(resp.cookies["access_token"].value, "")
