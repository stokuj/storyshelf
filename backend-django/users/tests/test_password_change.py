from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

USER_PASSWORD = "password123"


class PasswordChangeTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@test.com",
            handle="testuser",
            password=USER_PASSWORD,
        )

    def test_change_password_returns_204(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(
            "/api/users/me/password/",
            {"current_password": USER_PASSWORD, "new_password": "newsecurepass1"},
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_change_password_wrong_current_returns_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(
            "/api/users/me/password/",
            {"current_password": "wrongpassword", "new_password": "newsecurepass1"},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("current_password", resp.data)

    def test_change_password_updates_db(self):
        self.client.force_authenticate(user=self.user)
        self.client.patch(
            "/api/users/me/password/",
            {"current_password": USER_PASSWORD, "new_password": "newsecurepass1"},
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newsecurepass1"))

    def test_change_password_blacklists_old_token(self):
        refresh = RefreshToken.for_user(self.user)
        token_jti = refresh.payload["jti"]
        self.client.force_authenticate(user=self.user)
        self.client.patch(
            "/api/users/me/password/",
            {"current_password": USER_PASSWORD, "new_password": "newsecurepass1"},
        )
        outstanding = OutstandingToken.objects.get(jti=token_jti)
        self.assertTrue(BlacklistedToken.objects.filter(token=outstanding).exists())

    def test_change_password_issues_new_cookies(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(
            "/api/users/me/password/",
            {"current_password": USER_PASSWORD, "new_password": "newsecurepass1"},
        )
        self.assertIn("access_token", resp.cookies)
        self.assertNotEqual(resp.cookies["access_token"].value, "")

    def test_change_password_unauthenticated_returns_401(self):
        resp = self.client.patch(
            "/api/users/me/password/",
            {"current_password": USER_PASSWORD, "new_password": "newsecurepass1"},
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
