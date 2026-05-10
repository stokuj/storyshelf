package com.stokuj.books.integration.kafka;

import ch.qos.logback.classic.Level;
import ch.qos.logback.classic.Logger;
import ch.qos.logback.classic.spi.ILoggingEvent;
import ch.qos.logback.core.read.ListAppender;
import com.stokuj.books.integration.processor.NerResultProcessor;
import com.stokuj.books.integration.processor.RelationsResultProcessor;
import com.stokuj.books.book.book.BookRepository;
import com.stokuj.books.book.chapter.BookChapterRepository;
import com.stokuj.books.book.chapter.Chapter;
import com.stokuj.books.book.character.relation.StoryCharacterRelationRepository;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.slf4j.LoggerFactory;

import java.lang.reflect.Field;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class AnalysisResultConsumerTest {

    @Mock BookChapterRepository chapterRepository;
    @Mock BookRepository bookRepository;
    @Mock NerResultProcessor nerResultProcessor;
    @Mock RelationsResultProcessor relationsResultProcessor;
    @Mock StoryCharacterRelationRepository characterRelationRepository;

    @InjectMocks AnalysisResultConsumer consumer;

    private ListAppender<ILoggingEvent> listAppender;

    @BeforeEach
    void setUp() {
        Logger logger = (Logger) LoggerFactory.getLogger(AnalysisResultConsumer.class);
        listAppender = new ListAppender<>();
        listAppender.start();
        logger.addAppender(listAppender);
    }

    @AfterEach
    void tearDown() {
        Logger logger = (Logger) LoggerFactory.getLogger(AnalysisResultConsumer.class);
        logger.detachAppender(listAppender);
    }

    @Test
    void shouldLogWarningWhenStatsFieldsAreMissing() {
        Chapter chapter = chapter(1L);
        Map<String, Object> analysis = Map.of();
        Map<String, Object> payload = Map.of("chapterId", 1, "analysis", analysis);
        given(chapterRepository.findById(1L)).willReturn(Optional.of(chapter));

        consumer.consumeAnalyseResult(payload);

        List<ILoggingEvent> warnings = listAppender.list.stream()
                .filter(e -> e.getLevel() == Level.WARN)
                .toList();
        assertThat(warnings).anyMatch(e -> e.getFormattedMessage().contains("Missing char_count"));
        assertThat(warnings).anyMatch(e -> e.getFormattedMessage().contains("Missing word_count"));
    }

    @Test
    void shouldNotLogWarningWhenStatsFieldsArePresent() {
        Chapter chapter = chapter(1L);
        Map<String, Object> analysis = Map.of(
                "char_count", 5000,
                "char_count_clean", 4800,
                "word_count", 800,
                "token_count", 950
        );
        Map<String, Object> payload = Map.of("chapterId", 1, "analysis", analysis);
        given(chapterRepository.findById(1L)).willReturn(Optional.of(chapter));

        consumer.consumeAnalyseResult(payload);

        List<ILoggingEvent> warnings = listAppender.list.stream()
                .filter(e -> e.getLevel() == Level.WARN)
                .toList();
        assertThat(warnings).isEmpty();
    }

    @Test
    void shouldSetCharCountCorrectlyWhenPresent() {
        Chapter chapter = chapter(1L);
        Map<String, Object> analysis = Map.of("char_count", 5000);
        Map<String, Object> payload = Map.of("chapterId", 1, "analysis", analysis);
        given(chapterRepository.findById(1L)).willReturn(Optional.of(chapter));

        consumer.consumeAnalyseResult(payload);

        verify(chapterRepository).save(chapter);
        assertThat(chapter.getCharCount()).isEqualTo(5000);
    }

    private Chapter chapter(Long id) {
        Chapter chapter = new Chapter();
        setField(chapter, "id", id);
        setField(chapter, "analysisCompleted", false);
        return chapter;
    }

    private void setField(Object target, String fieldName, Object value) {
        try {
            Field field = target.getClass().getDeclaredField(fieldName);
            field.setAccessible(true);
            field.set(target, value);
        } catch (ReflectiveOperationException e) {
            throw new RuntimeException(e);
        }
    }
}
