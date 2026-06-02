from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"
REFRESH_COOKIE_PATH = "/api/auth/refresh/"


class JWTCookieAuthentication(JWTAuthentication):
    """Reads JWT from HttpOnly cookie instead of Authorization header."""

    def authenticate(self, request):
        raw_token = request.COOKIES.get(ACCESS_COOKIE)
        if raw_token is None:
            # Fallback to Authorization header (ADR-001 compliance)
            header = request.META.get("HTTP_AUTHORIZATION", "")
            if header.startswith("Bearer "):
                raw_token = header[7:]
            else:
                return None
        try:
            validated_token = self.get_validated_token(raw_token)
        except InvalidToken:
            return None
        return self.get_user(validated_token), validated_token


def _cookie_flags() -> dict:
    """Pull cross-origin cookie flags from Django settings (env-driven, see settings/base.py)."""
    flags = {
        "samesite": getattr(settings, "JWT_COOKIE_SAMESITE", "Lax"),
        "secure": getattr(settings, "JWT_COOKIE_SECURE", False),
    }
    domain = getattr(settings, "JWT_COOKIE_DOMAIN", None)
    if domain:
        flags["domain"] = domain
    return flags


def set_jwt_cookies(response, access_token, refresh_token=None):
    """Set HttpOnly JWT cookies on response. access/refresh can be token objects or strings."""
    access_max_age = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()
    refresh_max_age = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()
    flags = _cookie_flags()

    response.set_cookie(
        ACCESS_COOKIE,
        str(access_token),
        httponly=True,
        max_age=access_max_age,
        **flags,
    )
    if refresh_token is not None:
        response.set_cookie(
            REFRESH_COOKIE,
            str(refresh_token),
            httponly=True,
            max_age=refresh_max_age,
            path=REFRESH_COOKIE_PATH,
            **flags,
        )


def clear_jwt_cookies(response):
    """Expire both JWT cookies.

    The deletion cookie must carry the same domain/samesite as the original,
    otherwise the browser treats it as a different cookie and the real one
    survives logout (matters whenever JWT_COOKIE_DOMAIN / a non-default
    SameSite are configured).
    """
    flags = _cookie_flags()
    domain = flags.get("domain")
    samesite = flags["samesite"]
    response.delete_cookie(ACCESS_COOKIE, domain=domain, samesite=samesite)
    response.delete_cookie(
        REFRESH_COOKIE, path=REFRESH_COOKIE_PATH, domain=domain, samesite=samesite
    )
