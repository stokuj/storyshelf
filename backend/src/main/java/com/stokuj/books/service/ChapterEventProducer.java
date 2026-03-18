package com.stokuj.books.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

@Slf4j
@Service
public class ChapterEventProducer {

    private final KafkaTemplate<Object, Object> kafkaTemplate;
    private static final String TOPIC = "chapter.analyse";

    public ChapterEventProducer(KafkaTemplate<Object, Object> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    public void sendChapterForAnalysis(Long chapterId, String content) {
        log.info("Sending chapter {} to topic {} for analysis", chapterId, TOPIC);
        
        Map<String, Object> payload = new HashMap<>();
        payload.put("chapterId", chapterId);
        payload.put("content", content);
        
        kafkaTemplate.send(TOPIC, String.valueOf(chapterId), payload);
    }
}
