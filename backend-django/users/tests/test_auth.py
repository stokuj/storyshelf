from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class RegisterTest(APITestCase):
    def setUp(self):
        self.url = "/api/auth/register/"

    def test_post_valid_returns_201_with_cookies(self):
        resp = self.client.post(
            self.url,
            {"email": "new@test.com", "handle": "newuser", "password": "secret123"},
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("access_token", resp.cookies)
        self.assertIn("refresh_token", resp.cookies)
        self.assertTrue(resp.cookies["access_token"]["httponly"])
        self.assertEqual(resp.data["authenticated"], True)
        self.assertEqual(resp.data["email"], "new@test.com")
        self.assertTrue(User.objects.filter(email="new@test.com").exists())

    def test_post_duplicate_email_returns_400(self):
        User.objects.create_user(email="dup@test.com", handle="dupuser", password="pw")
        resp = self.client.post(
            self.url,
            {"email": "dup@test.com", "handle": "another", "password": "secret123"},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_duplicate_username_returns_400(self):
        User.objects.create_user(email="a@test.com", handle="dupuser", password="pw")
        resp = self.client.post(
            self.url,
            {"email": "b@test.com", "handle": "dupuser", "password": "secret123"},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_missing_email_returns_400(self):
        resp = self.client.post(self.url, {"handle": "someone", "password": "secret123"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_short_password_returns_400(self):
        resp = self.client.post(
            self.url,
            {"email": "x@test.com", "handle": "someone", "password": "12345"},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_invalid_username_uppercase_returns_400(self):
        resp = self.client.post(
            self.url,
            {"email": "x@test.com", "handle": "BadUser", "password": "secret123"},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_empty_body_returns_400(self):
        resp = self.client.post(self.url, {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTest(APITestCase):
    def setUp(self):
        self.url = "/api/auth/login/"
        self.user = User.objects.create_user(
            email="login@test.com", handle="loginuser", password="secret123"
        )

    def test_post_valid_returns_200_with_cookies(self):
        resp = self.client.post(
            self.url, {"email": "login@test.com", "password": "secret123"}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", resp.cookies)
        self.assertIn("refresh_token", resp.cookies)
        self.assertTrue(resp.cookies["access_token"]["httponly"])
        self.assertEqual(resp.data["authenticated"], True)

    def test_post_wrong_password_returns_400(self):
        resp = self.client.post(
            self.url, {"email": "login@test.com", "password": "wrongpass"}
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_nonexistent_email_returns_400(self):
        resp = self.client.post(self.url, {"email": "no@test.com", "password": "secret123"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_missing_fields_returns_400(self):
        resp = self.client.post(self.url, {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_inactive_user_returns_400(self):
        self.user.is_active = False
        self.user.save()
        resp = self.client.post(
            self.url, {"email": "login@test.com", "password": "secret123"}
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class TokenRefreshTest(APITestCase):
    def setUp(self):
        self.url = "/api/auth/refresh/"
        self.user = User.objects.create_user(
            email="refresh@test.com", handle="refreshuser", password="secret123"
        )

    def _login(self):
        self.client.post(
            "/api/auth/login/",
            {"email": "refresh@test.com", "password": "secret123"},
        )

    def test_post_with_cookie_returns_200_and_new_cookies(self):
        self._login()
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", resp.cookies)

    def test_post_without_cookie_returns_401(self):
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutTest(APITestCase):
    def setUp(self):
        self.url = "/api/auth/logout/"
        User.objects.create_user(
            email="logout@test.com", handle="logoutuser", password="secret123"
        )

    def _login(self):
        self.client.post(
            "/api/auth/login/",
            {"email": "logout@test.com", "password": "secret123"},
        )

    def test_post_clears_cookies_and_returns_200(self):
        self._login()
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["message"], "Logged out successfully")
        if "access_token" in resp.cookies:
            self.assertEqual(resp.cookies["access_token"]["max-age"], 0)

    def test_post_no_cookie_still_succeeds_200(self):
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class AuthMeTest(APITestCase):
    def setUp(self):
        self.url = "/api/auth/me/"
        self.user = User.objects.create_user(
            email="me@test.com", handle="meuser", password="secret123"
        )

    def _login(self):
        self.client.post(
            "/api/auth/login/",
            {"email": "me@test.com", "password": "secret123"},
        )

    def test_get_authenticated_via_cookie_returns_200_with_user_data(self):
        self._login()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["authenticated"])
        self.assertEqual(resp.data["email"], "me@test.com")
        self.assertEqual(resp.data["handle"], "meuser")

    def test_get_unauthenticated_returns_200_with_false(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["authenticated"])
        self.assertIsNone(resp.data["email"])
