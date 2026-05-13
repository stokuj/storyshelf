from .base import *  # noqa: F401, F403

DEBUG = True
SECRET_KEY = "dev-not-for-production"
CELERY_TASK_ALWAYS_EAGER = True
CORS_ALLOW_ALL_ORIGINS = True
CSRF_TRUSTED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
