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
    private static final String TOPIC_FIND_PAIRS = "chapter.find-pairs";
    private static final String TOPIC_RELATIONS = "chapter.relations";

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

    public void sendChapterForRelations(Long chapterId, String content, List<String> names) {
        log.info("Sending chapter {} to topic {} for relations", chapterId, TOPIC_RELATIONS);

        Map<String, Object> payload = new HashMap<>();
        payload.put("chapterId", chapterId);
        payload.put("content", content);
        payload.put("names", names);

        kafkaTemplate.send(TOPIC_RELATIONS, String.valueOf(chapterId), payload);
    }

    public void sendChapterForFindPairs(Long chapterId, String content, java.util.List<String> names) {
        log.info("Sending chapter {} to topic {} for find-pairs", chapterId, TOPIC_FIND_PAIRS);
        
        Map<String, Object> payload = new HashMap<>();
        payload.put("chapterId", chapterId);
        payload.put("content", content);
        payload.put("names", names);
        
        kafkaTemplate.send(TOPIC_FIND_PAIRS, String.valueOf(chapterId), payload);
    }
}
