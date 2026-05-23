from rest_framework import status
from rest_framework.test import APITestCase

from config.test_helpers import AuthTestHelper
from users.models import User


class RegisterEdgeCaseTest(AuthTestHelper, APITestCase):
    """Edge cases around user registration that guard against 500s and data leaks."""

    def setUp(self):
        self.url = "/api/auth/register/"

    def test_duplicate_email_returns_400_not_500(self):
        User.objects.create_user(email="dup@test.com", username="dupuser", password="pw")
        resp = self.client.post(
            self.url,
            {"email": "dup@test.com", "username": "another", "password": "secret123"},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", resp.data)

    def test_duplicate_email_case_insensitive_fails(self):
        User.objects.create_user(email="UPPER@test.com", username="upperuser", password="pw")
        resp = self.client.post(
            self.url,
            {"email": "upper@test.com", "username": "another", "password": "secret123"},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_not_leaked_in_response(self):
        resp = self.client.post(
            self.url,
            {"email": "leak@test.com", "username": "leakuser", "password": "secret123"},
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        raw = resp.content.decode()
        self.assertNotIn("secret123", raw)

    def test_username_too_short_returns_400(self):
        resp = self.client.post(
            self.url,
            {"email": "short@test.com", "username": "ab", "password": "secret123"},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_username_non_ascii_returns_400(self):
        resp = self.client.post(
            self.url,
            {"email": "ascii@test.com", "username": "tëst", "password": "secret123"},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class RefreshEdgeCaseTest(APITestCase):
    """Edge cases for token refresh endpoint."""

    def setUp(self):
        self.url = "/api/auth/refresh/"

    def test_malformed_refresh_cookie_returns_401(self):
        self.client.cookies["refresh_token"] = "not.a.jwt"
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expired_refresh_cookie_returns_401(self):
        # a well-formed but expired/invalid token string
        self.client.cookies["refresh_token"] = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ."
            "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        )
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
