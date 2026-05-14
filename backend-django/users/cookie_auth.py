import os

from rest_framework_simplejwt.authentication import JWTAuthentication

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"
REFRESH_COOKIE_PATH = "/api/auth/refresh/"


class JWTCookieAuthentication(JWTAuthentication):
    """Reads JWT from HttpOnly cookie instead of Authorization header."""

    def authenticate(self, request):
        raw_token = request.COOKIES.get(ACCESS_COOKIE)
        if raw_token is None:
            return None
        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token


def set_jwt_cookies(response, access_token, refresh_token=None):
    """Set HttpOnly JWT cookies on response. access/refresh can be token objects or strings."""
    secure = os.getenv("DJANGO_ENV", "dev") == "prod"
    access_max_age = int(os.getenv("JWT_ACCESS_LIFETIME_MINUTES", "30")) * 60
    refresh_max_age = int(os.getenv("JWT_REFRESH_LIFETIME_MINUTES", "1440")) * 60

    response.set_cookie(
        ACCESS_COOKIE,
        str(access_token),
        httponly=True,
        samesite="Lax",
        secure=secure,
        max_age=access_max_age,
    )
    if refresh_token is not None:
        response.set_cookie(
            REFRESH_COOKIE,
            str(refresh_token),
            httponly=True,
            samesite="Lax",
            secure=secure,
            max_age=refresh_max_age,
            path=REFRESH_COOKIE_PATH,
        )


def clear_jwt_cookies(response):
    """Expire both JWT cookies."""
    response.delete_cookie(ACCESS_COOKIE)
    response.delete_cookie(REFRESH_COOKIE, path=REFRESH_COOKIE_PATH)
