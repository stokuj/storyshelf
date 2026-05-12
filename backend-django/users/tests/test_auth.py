from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class RegisterTest(APITestCase):
    def setUp(self):
        self.url = "/api/auth/register/"

    def test_post_valid_returns_201_with_tokens(self):
        resp = self.client.post(
            self.url,
            {
                "email": "new@test.com",
                "username": "newuser",
                "password": "secret123",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)
        self.assertTrue(User.objects.filter(email="new@test.com").exists())

    def test_post_duplicate_email_returns_400(self):
        User.objects.create_user(email="dup@test.com", username="dupuser", password="pw")
        resp = self.client.post(
            self.url,
            {
                "email": "dup@test.com",
                "username": "another",
                "password": "secret123",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_duplicate_username_returns_400(self):
        User.objects.create_user(email="a@test.com", username="dupuser", password="pw")
        resp = self.client.post(
            self.url,
            {
                "email": "b@test.com",
                "username": "dupuser",
                "password": "secret123",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_missing_email_returns_400(self):
        resp = self.client.post(
            self.url,
            {
                "username": "someone",
                "password": "secret123",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_short_password_returns_400(self):
        resp = self.client.post(
            self.url,
            {
                "email": "x@test.com",
                "username": "someone",
                "password": "12345",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_invalid_username_uppercase_returns_400(self):
        resp = self.client.post(
            self.url,
            {
                "email": "x@test.com",
                "username": "BadUser",
                "password": "secret123",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_empty_body_returns_400(self):
        resp = self.client.post(self.url, {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTest(APITestCase):
    def setUp(self):
        self.url = "/api/auth/login/"
        self.user = User.objects.create_user(
            email="login@test.com",
            username="loginuser",
            password="secret123",
        )

    def test_post_valid_returns_200_with_tokens(self):
        resp = self.client.post(
            self.url,
            {
                "email": "login@test.com",
                "password": "secret123",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_post_wrong_password_returns_400(self):
        resp = self.client.post(
            self.url,
            {
                "email": "login@test.com",
                "password": "wrongpass",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_nonexistent_email_returns_400(self):
        resp = self.client.post(
            self.url,
            {
                "email": "no@test.com",
                "password": "secret123",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_missing_fields_returns_400(self):
        resp = self.client.post(self.url, {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_inactive_user_returns_400(self):
        self.user.is_active = False
        self.user.save()
        resp = self.client.post(
            self.url,
            {
                "email": "login@test.com",
                "password": "secret123",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class TokenRefreshTest(APITestCase):
    def setUp(self):
        self.url = "/api/auth/refresh/"
        self.user = User.objects.create_user(
            email="refresh@test.com",
            username="refreshuser",
            password="secret123",
        )

    def _get_tokens(self):
        resp = self.client.post(
            "/api/auth/login/",
            {
                "email": "refresh@test.com",
                "password": "secret123",
            },
        )
        return resp.data["access"], resp.data["refresh"]

    def test_post_valid_refresh_returns_200_with_new_access(self):
        _, refresh = self._get_tokens()
        resp = self.client.post(self.url, {"refresh": refresh})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)

    def test_post_missing_refresh_returns_400(self):
        resp = self.client.post(self.url, {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_invalid_refresh_returns_401(self):
        resp = self.client.post(self.url, {"refresh": "invalid-token"})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutTest(APITestCase):
    def setUp(self):
        self.url = "/api/auth/logout/"
        User.objects.create_user(
            email="logout@test.com",
            username="logoutuser",
            password="secret123",
        )

    def _get_tokens(self):
        resp = self.client.post(
            "/api/auth/login/",
            {
                "email": "logout@test.com",
                "password": "secret123",
            },
        )
        return resp.data["access"], resp.data["refresh"]

    def test_post_valid_refresh_returns_200(self):
        _, refresh = self._get_tokens()
        resp = self.client.post(self.url, {"refresh": refresh})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["message"], "Logged out successfully")

        resp = self.client.post(self.url, {"refresh": refresh})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_post_no_refresh_still_succeeds_200(self):
        resp = self.client.post(self.url, {})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class AuthMeTest(APITestCase):
    def setUp(self):
        self.url = "/api/auth/me/"
        self.user = User.objects.create_user(
            email="me@test.com",
            username="meuser",
            password="secret123",
        )

    def _get_access_token(self):
        resp = self.client.post(
            "/api/auth/login/",
            {
                "email": "me@test.com",
                "password": "secret123",
            },
        )
        return resp.data["access"]

    def test_get_authenticated_returns_200_with_user_data(self):
        token = self._get_access_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["authenticated"])
        self.assertEqual(resp.data["email"], "me@test.com")
        self.assertEqual(resp.data["username"], "meuser")

    def test_get_unauthenticated_returns_200_with_false(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["authenticated"])
        self.assertIsNone(resp.data["email"])
