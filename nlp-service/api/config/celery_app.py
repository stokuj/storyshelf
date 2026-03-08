import os

from celery import Celery


broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", broker_url)

celery = Celery(
    "app",
    broker=broker_url,
    backend=result_backend,
)
