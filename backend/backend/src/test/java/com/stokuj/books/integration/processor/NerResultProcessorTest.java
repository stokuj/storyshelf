package com.stokuj.books.integration.processor;

import com.stokuj.books.integration.dto.NerResult;
import com.stokuj.books.integration.kafka.ChapterEventProducer;
import com.stokuj.books.book.book.Book;
import com.stokuj.books.book.book.BookRepository;
import com.stokuj.books.book.chapter.BookChapterRepository;
import com.stokuj.books.book.chapter.Chapter;
import com.stokuj.books.book.character.aggregation.BookCharacterAggregator;
import com.stokuj.books.book.character.relation.StoryCharacterRelationRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.lang.reflect.Field;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class NerResultProcessorTest {

    @Mock BookChapterRepository chapterRepository;
    @Mock BookRepository bookRepository;
    @Mock StoryCharacterRelationRepository characterRelationRepository;
    @Mock ChapterEventProducer chapterEventProducer;
    @Mock BookCharacterAggregator bookCharacterAggregator;

    @InjectMocks NerResultProcessor processor;

    @Test
    void shouldUseAtomicIncrementForNerCompletedCount() {
        Book book = book(1L, 3, 1);
        Chapter chapter = chapter(1L, book, 2);
        NerResult result = new NerResult(Map.of("Alice", 5));
        given(bookRepository.findByIdForUpdate(1L)).willReturn(Optional.of(book));

        processor.process(chapter, result);

        verify(bookRepository).incrementNerCompletedCount(1L);
    }

    @Test
    void shouldNotCallSaveAfterIncrement() {
        Book book = book(1L, 3, 1);
        Chapter chapter = chapter(1L, book, 2);
        NerResult result = new NerResult(Map.of("Alice", 5));
        given(bookRepository.findByIdForUpdate(1L)).willReturn(Optional.of(book));

        processor.process(chapter, result);

        verify(bookRepository, never()).save(any(Book.class));
    }

    @Test
    void shouldSendFindPairsWhenAllChaptersHaveNerResults() {
        Book book = book(1L, 3, 2);
        Chapter chapter = chapter(1L, book, 3);
        NerResult result = new NerResult(Map.of("Alice", 5));
        given(bookRepository.findByIdForUpdate(1L)).willReturn(Optional.of(book));
        given(characterRelationRepository.existsByBookId(1L)).willReturn(false);
        given(bookCharacterAggregator.toCharacterMap(1L)).willReturn(Map.of("Alice", 5));
        given(chapterRepository.findAllByBookIdOrderByChapterNumber(1L)).willReturn(List.of(chapter));

        processor.process(chapter, result);

        verify(chapterEventProducer).sendBookForFindPairs(eq(1L), anyString(), any());
    }

    @Test
    void shouldNotSendFindPairsIfRelationsAlreadyExist() {
        Book book = book(1L, 3, 2);
        Chapter chapter = chapter(1L, book, 3);
        NerResult result = new NerResult(Map.of("Alice", 5));
        given(bookRepository.findByIdForUpdate(1L)).willReturn(Optional.of(book));
        given(characterRelationRepository.existsByBookId(1L)).willReturn(true);

        processor.process(chapter, result);

        verify(chapterEventProducer, never()).sendBookForFindPairs(anyLong(), anyString(), any());
    }

    @Test
    void shouldSendFindPairsForChapterOneRegardlessOfCount() {
        Book book = book(1L, 10, 0);
        Chapter chapter = chapter(1L, book, 1);
        NerResult result = new NerResult(Map.of("Alice", 5));
        given(bookRepository.findByIdForUpdate(1L)).willReturn(Optional.of(book));
        given(characterRelationRepository.existsByBookId(1L)).willReturn(false);
        given(bookCharacterAggregator.toCharacterMap(1L)).willReturn(Map.of("Alice", 5));
        given(chapterRepository.findAllByBookIdOrderByChapterNumber(1L)).willReturn(List.of(chapter));

        processor.process(chapter, result);

        verify(chapterEventProducer).sendBookForFindPairs(eq(1L), anyString(), any());
    }

    private Book book(Long id, int chaptersCount, int nerCompletedCount) {
        Book book = new Book();
        setField(book, "id", id);
        setField(book, "chaptersCount", chaptersCount);
        setField(book, "nerCompletedCount", nerCompletedCount);
        return book;
    }

    private Chapter chapter(Long id, Book book, int chapterNumber) {
        Chapter chapter = new Chapter();
        setField(chapter, "id", id);
        setField(chapter, "book", book);
        setField(chapter, "chapterNumber", chapterNumber);
        setField(chapter, "content", "Sample content.");
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
