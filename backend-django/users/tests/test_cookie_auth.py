from unittest.mock import MagicMock, patch

from django.test import RequestFactory, TestCase
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import AccessToken

from users.cookie_auth import (
    ACCESS_COOKIE,
    REFRESH_COOKIE,
    REFRESH_COOKIE_PATH,
    JWTCookieAuthentication,
    clear_jwt_cookies,
    set_jwt_cookies,
)
from users.models import User


class JWTCookieAuthenticationTest(TestCase):
    def setUp(self):
        self.auth = JWTCookieAuthentication()
        self.user = User.objects.create_user(
            email="cookie@test.com", handle="cookieuser", password="secret123"
        )

    def test_no_cookie_returns_none(self):
        factory = RequestFactory()
        request = factory.get("/api/users/me/")
        result = self.auth.authenticate(request)
        self.assertIsNone(result)

    def test_invalid_token_format_returns_none(self):
        factory = RequestFactory()
        request = factory.get("/api/users/me/")
        request.COOKIES[ACCESS_COOKIE] = "not.a.jwt"
        result = self.auth.authenticate(request)
        self.assertIsNone(result)

    @patch("rest_framework_simplejwt.authentication.JWTAuthentication.get_validated_token")
    def test_expired_token_returns_none(self, mock_get_validated_token):
        mock_get_validated_token.side_effect = InvalidToken("Token is invalid or expired")
        factory = RequestFactory()
        request = factory.get("/api/users/me/")
        request.COOKIES[ACCESS_COOKIE] = "expired.token.here"
        result = self.auth.authenticate(request)
        self.assertIsNone(result)

    def test_valid_token_returns_user_and_token(self):
        token = AccessToken.for_user(self.user)
        factory = RequestFactory()
        request = factory.get("/api/users/me/")
        request.COOKIES[ACCESS_COOKIE] = str(token)
        result = self.auth.authenticate(request)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], self.user)


class SetJWTCookiesTest(TestCase):
    def test_sets_access_cookie_with_settings_samesite(self):
        response = MagicMock()
        set_jwt_cookies(response, "access_token_value")
        response.set_cookie.assert_called_once()
        args, kwargs = response.set_cookie.call_args
        self.assertEqual(args[0], ACCESS_COOKIE)
        self.assertEqual(args[1], "access_token_value")
        self.assertTrue(kwargs["httponly"])
        # Dev settings: SameSite=Lax, Secure=False, no domain
        self.assertEqual(kwargs["samesite"], "Lax")
        self.assertFalse(kwargs["secure"])

    def test_sets_both_cookies_when_refresh_provided(self):
        response = MagicMock()
        set_jwt_cookies(response, "access_value", "refresh_value")
        self.assertEqual(response.set_cookie.call_count, 2)
        calls = [c.args[0] for c in response.set_cookie.call_args_list]
        self.assertIn(ACCESS_COOKIE, calls)
        self.assertIn(REFRESH_COOKIE, calls)

    def test_refresh_cookie_has_correct_path(self):
        response = MagicMock()
        set_jwt_cookies(response, "access_value", "refresh_value")
        for call in response.set_cookie.call_args_list:
            if call.args[0] == REFRESH_COOKIE:
                self.assertEqual(call.kwargs["path"], REFRESH_COOKIE_PATH)
                break
        else:
            self.fail("Refresh cookie not set")

    def test_respects_overridden_samesite_and_secure(self):
        from django.test import override_settings

        response = MagicMock()
        with override_settings(JWT_COOKIE_SAMESITE="None", JWT_COOKIE_SECURE=True):
            set_jwt_cookies(response, "access_value", "refresh_value")
        for call in response.set_cookie.call_args_list:
            self.assertEqual(call.kwargs["samesite"], "None")
            self.assertTrue(call.kwargs["secure"])

    def test_passes_cookie_domain_when_set(self):
        from django.test import override_settings

        response = MagicMock()
        with override_settings(JWT_COOKIE_DOMAIN=".storyshelf.example.com"):
            set_jwt_cookies(response, "access_value", "refresh_value")
        for call in response.set_cookie.call_args_list:
            self.assertEqual(call.kwargs["domain"], ".storyshelf.example.com")


class ClearJWTCookiesTest(TestCase):
    def test_deletes_both_cookies(self):
        response = MagicMock()
        clear_jwt_cookies(response)
        self.assertEqual(response.delete_cookie.call_count, 2)
        calls = [c.args[0] for c in response.delete_cookie.call_args_list]
        self.assertIn(ACCESS_COOKIE, calls)
        self.assertIn(REFRESH_COOKIE, calls)

    def test_passes_cookie_domain_when_set(self):
        from django.test import override_settings

        response = MagicMock()
        with override_settings(JWT_COOKIE_DOMAIN=".storyshelf.example.com"):
            clear_jwt_cookies(response)
        # Deletion must target the same domain or the browser keeps the cookie.
        for call in response.delete_cookie.call_args_list:
            self.assertEqual(call.kwargs["domain"], ".storyshelf.example.com")
