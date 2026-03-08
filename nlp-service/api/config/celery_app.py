import os

from celery import Celery
from celery.signals import worker_process_init
from api.services.transformers import DEFAULT_NER_MODEL, load_ner_model

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", broker_url)


celery = Celery(
    "app",
    broker=broker_url,
    backend=result_backend,
)


@worker_process_init.connect
def init_worker(**kwargs):
    load_ner_model(DEFAULT_NER_MODEL)
