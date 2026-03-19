import json
import logging
import threading
from confluent_kafka import Consumer, KafkaError

from api.config import settings
from api.services.analyse_service import process_analyse
from api.services.find_pairs_service import process_find_pairs
from api.tasks.ner_task import extract_entities_task
from api.tasks.relations_task import extract_chapter_relations_task

logger = logging.getLogger(__name__)

class ChapterAnalysisConsumer(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.consumer = Consumer({
            'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
            'group.id': 'storyweave-analysis-group',
            'auto.offset.reset': 'earliest'
        })
        self._running = True

    def run(self):
        topics = ['chapter.analyse', 'chapter.ner', 'chapter.find-pairs', 'chapter.relations']
        self.consumer.subscribe(topics)
        logger.info(f"Started Kafka consumer on {settings.KAFKA_BOOTSTRAP_SERVERS}, topics: {topics}")

        while self._running:
            msg = self.consumer.poll(timeout=1.0)

            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    logger.error(f"Kafka error: {msg.error()}")
                    continue

            try:
                payload_str = msg.value().decode('utf-8')
                payload = json.loads(payload_str)
                
                chapter_id = payload.get('chapterId')
                content = payload.get('content')
                topic = msg.topic()
                
                if not chapter_id or not content:
                    logger.warning(f"Invalid payload received on {topic}, missing chapterId or content")
                    continue

                if topic == 'chapter.analyse':
                    logger.info(f"Analysing chapter {chapter_id}...")
                    process_analyse(content, chapter_id)
                    logger.info(f"Successfully processed chapter.analyse for {chapter_id}")

                elif topic == 'chapter.ner':
                    logger.info(f"Queueing NER task for chapter {chapter_id}...")
                    extract_entities_task.delay(content, chapter_id)
                    logger.info(f"Successfully queued chapter.ner for {chapter_id}")

                elif topic == 'chapter.relations':
                    names = payload.get('names', [])
                    logger.info(f"Queueing Relations task for chapter {chapter_id} with names {names}...")
                    extract_chapter_relations_task.delay(content, chapter_id, names if len(names) >= 2 else None)
                    logger.info(f"Successfully queued chapter.relations for {chapter_id}")

                elif topic == 'chapter.find-pairs':
                    names = payload.get('names', [])
                    logger.info(f"Finding pairs for chapter {chapter_id} with names {names}...")
                    process_find_pairs(content, names, chapter_id)
                    logger.info(f"Successfully processed chapter.find-pairs for {chapter_id}")

            except Exception as e:
                logger.error(f"Error processing kafka message from topic {msg.topic() if msg else 'unknown'}: {e}", exc_info=True)

        self.consumer.close()
        logger.info("Kafka consumer stopped")

    def stop(self):
        self._running = False
