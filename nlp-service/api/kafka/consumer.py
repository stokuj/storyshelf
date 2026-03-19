import json
import logging
import threading
from confluent_kafka import Consumer, KafkaError
import httpx

from api.config import settings
from api.services.book_service import analyse_text, find_sentences_with_both_characters
from api.tasks.ner_task import extract_entities_task

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
        topics = ['chapter.analyse', 'chapter.ner', 'chapter.find-pairs']
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
                # payload is JSON with chapterId and content
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
                    analysis_result = analyse_text(content)
                    
                    patch_url = f"{settings.SPRINGSHELF_BASE_URL}/api/fastAPI/chapters/{chapter_id}/analyse-result"
                    patch_payload = {"analysis": analysis_result}
                    
                    logger.info(f"Sending PATCH to {patch_url}")
                    response = httpx.patch(patch_url, json=patch_payload, timeout=10.0)
                    response.raise_for_status()
                    
                    logger.info(f"Successfully processed chapter.analyse for {chapter_id}")

                elif topic == 'chapter.ner':
                    logger.info(f"Queueing NER task for chapter {chapter_id}...")
                    # Dispatch to celery and pass the chapter_id so it can patch back to spring
                    extract_entities_task.delay(content, chapter_id)
                    logger.info(f"Successfully queued chapter.ner for {chapter_id}")

                elif topic == 'chapter.find-pairs':
                    names = payload.get('names', [])
                    logger.info(f"Finding pairs for chapter {chapter_id} with names {names}...")
                    pairs_result = find_sentences_with_both_characters(content, names)
                    
                    patch_url = f"{settings.SPRINGSHELF_BASE_URL}/api/fastAPI/chapters/{chapter_id}/find-pairs-result"
                    patch_payload = {"pairs": pairs_result}
                    
                    logger.info(f"Sending PATCH to {patch_url}")
                    response = httpx.patch(patch_url, json=patch_payload, timeout=10.0)
                    response.raise_for_status()
                    
                    logger.info(f"Successfully processed chapter.find-pairs for {chapter_id}")

            except Exception as e:
                logger.error(f"Error processing kafka message from topic {msg.topic() if msg else 'unknown'}: {e}", exc_info=True)

    def stop(self):
        self._running = False
        self.consumer.close()
        logger.info("Kafka consumer stopped")
