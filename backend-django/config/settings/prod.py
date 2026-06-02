import os

from .base import *  # noqa: F401, F403

DEBUG = False

# Behind Caddy (TLS terminated upstream)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Caddy already redirects HTTP -> HTTPS; keeping Django redirect on
# would loop because forwarded requests look like plain HTTP without
# SECURE_PROXY_SSL_HEADER. With the header above set, this is safe.
SECURE_SSL_REDIRECT = True

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "false").lower() == "true"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

CORS_ALLOWED_ORIGINS = [o for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o]

# JWT cookies prod: same-origin za Caddy (front + /api z jednego origin, ADR-002).
# SameSite=Lax wystarcza i jest jedyna ochrona CSRF dla JWTCookieAuthentication
# (DRF nie wymusza tokenu CSRF dla tej klasy). Cross-origin (SameSite=None) tylko
# swiadomie przez env — wtedy wymaga JWT_COOKIE_SECURE i osobnej ochrony CSRF.
JWT_COOKIE_SAMESITE = os.getenv("JWT_COOKIE_SAMESITE", "Lax")
JWT_COOKIE_SECURE = os.getenv("JWT_COOKIE_SECURE", "true").lower() == "true"
JWT_COOKIE_DOMAIN = os.getenv("JWT_COOKIE_DOMAIN") or None

# SameSite=None bez Secure jest odrzucane przez przegladarki. Fail fast.
if JWT_COOKIE_SAMESITE == "None" and not JWT_COOKIE_SECURE:
    raise ValueError(
        "JWT_COOKIE_SECURE must be true when JWT_COOKIE_SAMESITE=None (browsers reject otherwise)"
    )

CSRF_TRUSTED_ORIGINS = [o for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if o]
if not CSRF_TRUSTED_ORIGINS:
    # Empty in prod means every cookie-authenticated POST will 403.
    # Fail fast at boot instead of silently in the first request.
    raise ValueError("CSRF_TRUSTED_ORIGINS env var required in production")
