package com.stokuj.books.book.chapter;

import com.stokuj.books.book.book.Book;
import com.stokuj.books.book.book.BookRepository;
import com.stokuj.books.book.chapter.dto.ChapterResponse;
import com.stokuj.books.book.character.aggregation.BookCharacterRepository;
import com.stokuj.books.book.character.relation.StoryCharacterRelationRepository;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.integration.kafka.ChapterEventProducer;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class BookChapterServiceTest {

    @Mock
    BookChapterRepository chapterRepository;

    @Mock
    BookRepository bookRepository;

    @Mock
    BookCharacterRepository bookCharacterRepository;

    @Mock
    StoryCharacterRelationRepository characterRelationRepository;

    @Mock
    ChapterEventProducer chapterEventProducer;

    @InjectMocks
    BookChapterService bookChapterService;

    @Nested
    class LoadContent {

        @Test
        void shouldThrowWhenBookNotFound() {
            given(bookRepository.findById(404L)).willReturn(Optional.empty());

            assertThatThrownBy(() -> bookChapterService.loadContent(404L, "Chapter 1\nText"))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("Book not found");
        }

        @Test
        void shouldLoadContentAndSendEvents() {
            Long bookId = 1L;
            Book book = book(bookId);
            String text = "Chapter 1\n" + "a".repeat(2500) + "\n\nChapter 2\n" + "b".repeat(2600);

            given(bookRepository.findById(bookId)).willReturn(Optional.of(book));
            given(chapterRepository.saveAll(org.mockito.ArgumentMatchers.anyList()))
                    .willAnswer(invocation -> {
                        List<Chapter> chapters = invocation.getArgument(0);
                        long id = 100L;
                        for (Chapter chapter : chapters) {
                            setField(chapter, "id", id++);
                        }
                        return chapters;
                    });
            given(chapterRepository.countByBookId(bookId)).willReturn(2);

            int created = bookChapterService.loadContent(bookId, text);

            assertThat(created).isEqualTo(2);
            verify(chapterRepository).deleteAllByBookId(bookId);
            verify(bookCharacterRepository).deleteAllByBookId(bookId);
            verify(characterRelationRepository).deleteAllByBookId(bookId);
            verify(bookRepository).save(book);
            assertThat(getField(book, "chaptersCount")).isEqualTo(2);
            assertThat(getField(book, "nerCompletedCount")).isEqualTo(0);

            ArgumentCaptor<List<Chapter>> captor = ArgumentCaptor.forClass(List.class);
            verify(chapterRepository).saveAll(captor.capture());
            List<Chapter> savedChapters = captor.getValue();
            assertThat(savedChapters).hasSize(2);
            assertThat(getField(savedChapters.get(0), "chapterNumber")).isEqualTo(1);
            assertThat(getField(savedChapters.get(1), "chapterNumber")).isEqualTo(2);

            verify(chapterEventProducer).sendChapterForAnalysis(100L, (String) getField(savedChapters.get(0), "content"));
            verify(chapterEventProducer).sendChapterForAnalysis(101L, (String) getField(savedChapters.get(1), "content"));
            verify(chapterEventProducer).sendChapterForNer(100L, (String) getField(savedChapters.get(0), "content"));
        }

        @Test
        void shouldFallbackToSingleChapterWhenNoHeader() {
            Long bookId = 2L;
            Book book = book(bookId);
            String text = "This is plain text without chapter header.";
            given(bookRepository.findById(bookId)).willReturn(Optional.of(book));
            given(chapterRepository.saveAll(org.mockito.ArgumentMatchers.anyList()))
                    .willAnswer(invocation -> {
                        List<Chapter> chapters = invocation.getArgument(0);
                        setField(chapters.getFirst(), "id", 200L);
                        return chapters;
                    });
            given(chapterRepository.countByBookId(bookId)).willReturn(1);

            int created = bookChapterService.loadContent(bookId, text);

            assertThat(created).isEqualTo(1);
        }
    }

    @Nested
    class ReadAndClear {

        @Test
        void shouldMapChapterEntitiesToDto() {
            Chapter chapter = new Chapter();
            setField(chapter, "id", 1L);
            setField(chapter, "book", book(10L));
            setField(chapter, "chapterNumber", null);
            setField(chapter, "title", "Chapter 1");
            setField(chapter, "analysisCompleted", null);
            setField(chapter, "charCount", null);
            setField(chapter, "charCountClean", null);
            setField(chapter, "wordCount", null);
            setField(chapter, "tokenCount", null);
            given(chapterRepository.findAllByBookIdOrderByChapterNumber(10L)).willReturn(List.of(chapter));

            List<ChapterResponse> result = bookChapterService.getChapters(10L);

            assertThat(result).hasSize(1);
            assertThat(result.getFirst().bookId()).isEqualTo(10L);
            assertThat(result.getFirst().chapterNumber()).isEqualTo(0);
            assertThat(result.getFirst().analysisCompleted()).isFalse();
            assertThat(result.getFirst().charCount()).isEqualTo(0);
            assertThat(result.getFirst().wordCount()).isEqualTo(0);
        }

        @Test
        void shouldClearContent() {
            bookChapterService.clearContent(77L);

            verify(chapterRepository).deleteAllByBookId(77L);
        }
    }

    private Book book(Long id) {
        Book book = new Book();
        setField(book, "id", id);
        setField(book, "bookAuthors", new ArrayList<>());
        setField(book, "bookTags", new ArrayList<>());
        return book;
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

    private Object getField(Object target, String fieldName) {
        try {
            Field field = target.getClass().getDeclaredField(fieldName);
            field.setAccessible(true);
            return field.get(target);
        } catch (ReflectiveOperationException e) {
            throw new RuntimeException(e);
        }
    }
}
