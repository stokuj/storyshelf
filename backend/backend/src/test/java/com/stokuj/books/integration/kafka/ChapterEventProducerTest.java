package com.stokuj.books.integration.kafka;

import com.stokuj.books.integration.dto.PairResult;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.kafka.core.KafkaTemplate;

import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class ChapterEventProducerTest {

    @Mock
    KafkaTemplate<Object, Object> kafkaTemplate;

    @InjectMocks
    ChapterEventProducer producer;

    @Test
    void shouldSendBookForRelationsWithTypedPairResultList() {
        List<PairResult> pairs = List.of(
                new PairResult(List.of("Alice", "Bob")),
                new PairResult(List.of("Alice", "Charlie"))
        );

        producer.sendBookForRelations(1L, pairs);

        @SuppressWarnings("unchecked")
        ArgumentCaptor<Map<String, Object>> captor = ArgumentCaptor.forClass(Map.class);
        verify(kafkaTemplate).send(
                org.mockito.ArgumentMatchers.eq("book.relations"),
                org.mockito.ArgumentMatchers.eq("1"),
                captor.capture()
        );

        Map<String, Object> payload = captor.getValue();
        assertThat(payload).containsEntry("bookId", 1L);
        assertThat(payload.get("pairs")).isEqualTo(pairs);
    }

    @Test
    void shouldHandleEmptyPairsList() {
        List<PairResult> pairs = List.of();

        producer.sendBookForRelations(1L, pairs);

        verify(kafkaTemplate).send(
                org.mockito.ArgumentMatchers.eq("book.relations"),
                org.mockito.ArgumentMatchers.eq("1"),
                org.mockito.ArgumentMatchers.any(Map.class)
        );
    }
}
