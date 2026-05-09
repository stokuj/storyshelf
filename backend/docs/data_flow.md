# Data Flow (SpringShelf)

This document describes how SpringShelf triggers and consumes NLP analysis in the current architecture.

## 1) Trigger point in Spring

1. Moderator uploads chapter content via `POST /api/books/{bookId}/chapters`.
2. Spring splits text into chapters and stores them in `book_chapters`.
3. Spring publishes Kafka events:
   - `chapter.analyse` for all created chapters
   - `chapter.ner` for the first chapter (initial character extraction)

Producer: `com.stokuj.books.integration.kafka.ChapterEventProducer`

## 2) Processing in worker service (StoryWeave)

StoryWeave consumes request topics and processes asynchronously:

- `chapter.analyse` -> text statistics
- `chapter.ner` -> entity extraction
- `book.find-pairs` -> candidate character pairs
- `book.relations` -> relation extraction with LLM

## 3) Result topics back to Spring

StoryWeave publishes results to:

- `chapter.analyse.results`
- `chapter.ner.results`
- `book.find-pairs.results`
- `book.relations.results`

Consumer in Spring: `com.stokuj.books.integration.kafka.AnalysisResultConsumer`

## 4) Persisting results in Spring

Spring processors persist and aggregate results:

- `NerResultProcessor` updates chapter NER JSON and book-level character aggregates.
- `RelationsResultProcessor` stores relation pairs and final relation metadata.
- `BookCharacterAggregator` updates mentions and character map for book-level graph.

## 5) Idempotency and failure handling

- Delivery model is at-least-once, so Spring consumer contains duplicate guards.
- Spring Kafka `DefaultErrorHandler` uses bounded retries and dead-letter publishing.
- When a payload is invalid or related entity is missing, message can be routed to DLT after retries.

## 6) Read model for frontend

Frontend reads aggregated state mainly from:

- `GET /api/books/{id}/details` (book + chapters + characters + relations + reviews + shelf entry)
- `GET /api/books/{bookId}/characters`
- `GET /api/books/{bookId}/relations`

This allows UI to remain responsive while NLP pipeline runs asynchronously.
