from .base import *  # noqa: F401, F403

DEBUG = True
SECRET_KEY = "dev-not-for-production"
CELERY_TASK_ALWAYS_EAGER = True
CORS_ALLOW_ALL_ORIGINS = True
