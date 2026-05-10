import json
import logging
import time

import httpx

from api.config import settings

logger = logging.getLogger(__name__)

TOPIC_ANALYSE_RESULTS = "chapter.analyse.results"
TOPIC_NER_RESULTS = "chapter.ner.results"
TOPIC_FIND_PAIRS_RESULTS = "book.find-pairs.results"
TOPIC_RELATIONS_RESULTS = "book.relations.results"

_TOPIC_TO_PATH = {
    TOPIC_ANALYSE_RESULTS: "/api/internal/chapters/{id}/analyse-result/",
    TOPIC_NER_RESULTS: "/api/internal/chapters/{id}/ner-result/",
    TOPIC_FIND_PAIRS_RESULTS: "/api/internal/books/{id}/find-pairs-result/",
    TOPIC_RELATIONS_RESULTS: "/api/internal/books/{id}/relations-result/",
}


def _post_callback(url: str, payload: dict, max_retries: int = 3) -> None:
    for attempt in range(max_retries):
        try:
            response = httpx.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(2**attempt)
            else:
                raise


def send_json(topic: str, key: str, payload: dict) -> None:
    callback_path = _TOPIC_TO_PATH[topic].format(id=key)
    url = f"{settings.CALLBACK_BASE_URL}{callback_path}"
    try:
        _post_callback(url, payload)
    except Exception:
        logger.exception("Callback to %s failed after retries", url)
