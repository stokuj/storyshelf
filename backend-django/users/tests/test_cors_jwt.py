"""CORS preflight + cookie flags w dev vs prod settings.

Nie testujemy prod settings przez DJANGO_ENV=prod (wymagaloby resetu modulu),
zamiast tego uzywamy override_settings aby zsymulowac cross-origin profile.
"""
from __future__ import annotations

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from users.models import User


class CorsPreflightTest(TestCase):
    """Preflight OPTIONS z Origin headerem zwraca Access-Control-Allow-* z credentials."""

    def setUp(self):
        self.client = APIClient()

    def test_options_preflight_returns_cors_headers(self):
        response = self.client.options(
            "/api/auth/login/",
            HTTP_ORIGIN="http://localhost:5174",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type",
        )
        # corsheaders middleware odpowiada 200 (a nie 405) na preflight
        self.assertIn(response.status_code, (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT))
        self.assertEqual(
            response.get("Access-Control-Allow-Origin"), "http://localhost:5174"
        )
        self.assertEqual(response.get("Access-Control-Allow-Credentials"), "true")


class LoginCookieFlagsDevTest(TestCase):
    """Login w dev settings: Set-Cookie bez Secure, SameSite=Lax."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="cors@test.com", handle="corsuser", password="secret123"
        )

    def test_dev_login_sets_lax_insecure_cookie(self):
        response = self.client.post(
            "/api/auth/login/",
            {"email": "cors@test.com", "password": "secret123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content[:300])
        set_cookie_headers = response.cookies
        self.assertIn("access_token", set_cookie_headers)
        access = set_cookie_headers["access_token"]
        # SameSite=Lax w dev
        self.assertEqual(access["samesite"], "Lax")
        # Secure puste/false w dev (http://localhost)
        self.assertFalse(access["secure"])


@override_settings(JWT_COOKIE_SAMESITE="None", JWT_COOKIE_SECURE=True)
class LoginCookieFlagsProdProfileTest(TestCase):
    """Symulacja prod settings: Set-Cookie z Secure i SameSite=None."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="cors2@test.com", handle="corsuser2", password="secret123"
        )

    def test_prod_profile_login_sets_none_secure_cookie(self):
        response = self.client.post(
            "/api/auth/login/",
            {"email": "cors2@test.com", "password": "secret123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content[:300])
        access = response.cookies["access_token"]
        self.assertEqual(access["samesite"], "None")
        self.assertTrue(access["secure"])
