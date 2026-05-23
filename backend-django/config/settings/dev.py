import sys

from .base import *  # noqa: F401, F403
from .base import REST_FRAMEWORK

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "django"]
# >=32 bytes silences InsecureKeyLengthWarning during tests
SECRET_KEY = "dev-not-for-production-padding-padding-padding"
CELERY_TASK_ALWAYS_EAGER = True
CORS_ALLOW_ALL_ORIGINS = True
# JWT cookies dev: same-origin (Vue 5173 + API 8000), brak HTTPS lokalnie
JWT_COOKIE_SAMESITE = "Lax"
JWT_COOKIE_SECURE = False
JWT_COOKIE_DOMAIN = None
CSRF_TRUSTED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]

# Throttle counters live in the default cache, which is in-process LocMemCache
# during the test run. Sequential test cases share the same counters and
# trip the limits set in base.py; disable throttling under `manage.py test`
# and `pytest` so each test gets a clean slate.
_IS_TEST_RUN = "test" in sys.argv or any("pytest" in a for a in sys.argv)
if _IS_TEST_RUN:
    REST_FRAMEWORK = {**REST_FRAMEWORK, "DEFAULT_THROTTLE_CLASSES": []}
