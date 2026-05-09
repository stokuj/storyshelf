import json
import logging

from confluent_kafka import Producer

from api.config import settings

logger = logging.getLogger(__name__)

TOPIC_ANALYSE_RESULTS = "chapter.analyse.results"
TOPIC_NER_RESULTS = "chapter.ner.results"
TOPIC_FIND_PAIRS_RESULTS = "book.find-pairs.results"
TOPIC_RELATIONS_RESULTS = "book.relations.results"

_producer = Producer({"bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS})


def _delivery_report(err, msg):
    if err is not None:
        logger.error("Kafka delivery failed for topic %s: %s", msg.topic(), err)


def send_json(topic: str, key: str, payload: dict) -> None:
    data = json.dumps(payload).encode("utf-8")
    _producer.produce(topic, key=key, value=data, callback=_delivery_report)
    _producer.flush()
