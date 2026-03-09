from celery import Celery
from celery.signals import worker_process_init

from api.config.settings import CELERY_BROKER_URL, CELERY_RESULT_BACKEND
from api.services.transformers_service import DEFAULT_NER_MODEL, load_ner_model


celery = Celery(
    "app",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)


@worker_process_init.connect
def init_worker(**kwargs):
    load_ner_model(DEFAULT_NER_MODEL)
