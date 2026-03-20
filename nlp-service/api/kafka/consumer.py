import asyncio
import json
import logging
import threading
from confluent_kafka import Consumer, KafkaError

from api.config import settings
from api.services.analyse_service import process_analyse
from api.services.relations_service import process_book_relations_async
from api.tasks.find_pairs_task import find_pairs_task
from api.tasks.ner_task import extract_entities_task

logger = logging.getLogger(__name__)
app_event_loop: asyncio.AbstractEventLoop | None = None

class ChapterAnalysisConsumer(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.consumer = Consumer({
            'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
            'group.id': 'storyweave-analysis-group',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False,
        })
        self._running = True

    def run(self):
        topics = ['chapter.analyse', 'chapter.ner', 'book.find-pairs', 'book.relations']
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
                
                topic = msg.topic()

                if topic == 'chapter.analyse':
                    chapter_id = payload.get('chapterId')
                    content = payload.get('content')
                    if not chapter_id or not content:
                        logger.warning(f"Invalid payload received on {topic}, missing chapterId or content")
                        continue
                    logger.info(f"Analysing chapter {chapter_id}...")
                    process_analyse(content, chapter_id)
                    logger.info(f"Successfully processed chapter.analyse for {chapter_id}")
                    self.consumer.commit(message=msg, asynchronous=False)

                elif topic == 'chapter.ner':
                    chapter_id = payload.get('chapterId')
                    content = payload.get('content')
                    if not chapter_id or not content:
                        logger.warning(f"Invalid payload received on {topic}, missing chapterId or content")
                        continue
                    logger.info(f"Queueing NER task for chapter {chapter_id}...")
                    extract_entities_task.delay(content, chapter_id)
                    logger.info(f"Successfully queued chapter.ner for {chapter_id}")
                    self.consumer.commit(message=msg, asynchronous=False)

                elif topic == 'book.find-pairs':
                    book_id = payload.get('bookId')
                    content = payload.get('content')
                    characters = payload.get('characters', {})
                    names = list(characters.keys())
                    if not book_id or not content:
                        logger.warning(f"Invalid payload received on {topic}, missing bookId or content")
                        continue
                    logger.info(f"Queueing find-pairs task for book {book_id} with {len(names)} characters...")
                    find_pairs_task.delay(content, names, book_id)
                    logger.info(f"Successfully queued book.find-pairs for {book_id}")
                    self.consumer.commit(message=msg, asynchronous=False)

                elif topic == 'book.relations':
                    book_id = payload.get('bookId')
                    pairs = payload.get('pairs', [])
                    if not book_id:
                        logger.warning(f"Invalid payload received on {topic}, missing bookId")
                        continue
                    if app_event_loop is None:
                        logger.error("No app event loop available to process book.relations")
                        continue
                    logger.info(f"Queueing relations extraction for book {book_id}...")
                    asyncio.run_coroutine_threadsafe(
                        process_book_relations_async(pairs, book_id),
                        app_event_loop,
                    )
                    logger.info(f"Successfully scheduled book.relations for {book_id}")
                    self.consumer.commit(message=msg, asynchronous=False)

            except Exception as e:
                logger.error(f"Error processing kafka message from topic {msg.topic() if msg else 'unknown'}: {e}", exc_info=True)

        self.consumer.close()
        logger.info("Kafka consumer stopped")

    def stop(self):
        self._running = False
