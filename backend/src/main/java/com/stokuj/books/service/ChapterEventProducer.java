package com.stokuj.books.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
public class ChapterEventProducer {

    private final KafkaTemplate<Object, Object> kafkaTemplate;
    private static final String TOPIC_ANALYSE = "chapter.analyse";
    private static final String TOPIC_NER = "chapter.ner";
    private static final String TOPIC_BOOK_FIND_PAIRS = "book.find-pairs";
    private static final String TOPIC_BOOK_RELATIONS = "book.relations";

    public ChapterEventProducer(KafkaTemplate<Object, Object> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    public void sendChapterForAnalysis(Long chapterId, String content) {
        log.info("Sending chapter {} to topic {} for analysis", chapterId, TOPIC_ANALYSE);
        
        Map<String, Object> payload = new HashMap<>();
        payload.put("chapterId", chapterId);
        payload.put("content", content);
        
        kafkaTemplate.send(TOPIC_ANALYSE, String.valueOf(chapterId), payload);
    }

    public void sendChapterForNer(Long chapterId, String content) {
        log.info("Sending chapter {} to topic {} for NER", chapterId, TOPIC_NER);
        
        Map<String, Object> payload = new HashMap<>();
        payload.put("chapterId", chapterId);
        payload.put("content", content);
        
        kafkaTemplate.send(TOPIC_NER, String.valueOf(chapterId), payload);
    }

    public void sendBookForFindPairs(Long bookId, String fullContent, Map<String, Integer> characters) {
        log.info("Sending book {} to topic {} for find-pairs", bookId, TOPIC_BOOK_FIND_PAIRS);

        Map<String, Object> payload = new HashMap<>();
        payload.put("bookId", bookId);
        payload.put("content", fullContent);
        payload.put("characters", characters);

        kafkaTemplate.send(TOPIC_BOOK_FIND_PAIRS, String.valueOf(bookId), payload);
    }

    public void sendBookForRelations(Long bookId, List<?> pairs) {
        log.info("Sending book {} to topic {} for relations", bookId, TOPIC_BOOK_RELATIONS);

        Map<String, Object> payload = new HashMap<>();
        payload.put("bookId", bookId);
        payload.put("pairs", pairs);

        kafkaTemplate.send(TOPIC_BOOK_RELATIONS, String.valueOf(bookId), payload);
    }
}
