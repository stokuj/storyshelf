# Backend P1 Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 4 backend bugs: atomic NER counter, per-relation dedup, missing stats validation, and Kafka PairResult serializer type.

**Architecture:** Four independent fixes touching the Kafka integration pipeline (producers, consumers, processors). Each fix modifies 1-2 production files and adds unit tests with Mockito + AssertJ following existing project conventions.

**Tech Stack:** Java 21, Spring Boot 4.0.3, JUnit 5 + Mockito + AssertJ, Maven

**Base directory for all paths:** `backend/backend/`

---

## File Structure

| File | Action | Fix # |
|------|--------|-------|
| `src/main/java/com/stokuj/books/book/book/BookRepository.java` | Modify | 1 |
| `src/main/java/com/stokuj/books/integration/processor/NerResultProcessor.java` | Modify | 1 |
| `src/main/java/com/stokuj/books/integration/kafka/AnalysisResultConsumer.java` | Modify | 2, 3 |
| `src/main/java/com/stokuj/books/integration/processor/RelationsResultProcessor.java` | Modify | 2 |
| `src/main/java/com/stokuj/books/integration/kafka/ChapterEventProducer.java` | Modify | 4 |
| `src/test/java/com/stokuj/books/integration/processor/NerResultProcessorTest.java` | Create | 1 |
| `src/test/java/com/stokuj/books/integration/processor/RelationsResultProcessorTest.java` | Create | 2 |
| `src/test/java/com/stokuj/books/integration/kafka/AnalysisResultConsumerTest.java` | Create | 3 |
| `src/test/java/com/stokuj/books/integration/kafka/ChapterEventProducerTest.java` | Create | 4 |

---

### Task 1: Atomic NER Completed Counter

**Files:**
- Modify: `src/main/java/com/stokuj/books/book/book/BookRepository.java`
- Modify: `src/main/java/com/stokuj/books/integration/processor/NerResultProcessor.java`
- Create: `src/test/java/com/stokuj/books/integration/processor/NerResultProcessorTest.java`

- [ ] **Step 1: Add atomic increment query to BookRepository**

Open `src/main/java/com/stokuj/books/book/book/BookRepository.java` and add the import and method:

```java
package com.stokuj.books.book.book;

import com.stokuj.books.book.book.Book;
import jakarta.persistence.LockModeType;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface BookRepository extends JpaRepository<Book, Long> {
    @Query("SELECT DISTINCT b FROM Book b LEFT JOIN b.bookAuthors ba LEFT JOIN ba.author a LEFT JOIN b.genres g WHERE lower(b.title) LIKE lower(concat('%',:title,'%')) OR lower(a.name) LIKE lower(concat('%',:author,'%')) OR lower(g) LIKE lower(concat('%',:genre,'%'))")
    List<Book> searchByTitleAuthorOrGenre(String title, String author, String genre);

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("SELECT b FROM Book b WHERE b.id = :id")
    Optional<Book> findByIdForUpdate(Long id);

    @Modifying
    @Query("UPDATE Book b SET b.nerCompletedCount = b.nerCompletedCount + 1 WHERE b.id = :id")
    void incrementNerCompletedCount(@Param("id") Long id);
}
```

- [ ] **Step 2: Write failing test for NerResultProcessor**

```bash
mvn test -pl . -Dtest="NerResultProcessorTest" -DfailIfNoTests=false
```

Expected: FAIL (no tests yet)

Create `src/test/java/com/stokuj/books/integration/processor/NerResultProcessorTest.java`:

```java
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
        given(characterRelationRepository.existsByBookId(1L)).willReturn(true);
        given(chapterRepository.findAllByBookIdOrderByChapterNumber(1L)).willReturn(List.of(chapter));

        processor.process(chapter, result);

        verify(bookRepository).incrementNerCompletedCount(1L);
    }

    @Test
    void shouldNotCallSaveAfterIncrement() {
        Book book = book(1L, 3, 1);
        Chapter chapter = chapter(1L, book, 2);
        NerResult result = new NerResult(Map.of("Alice", 5));
        given(bookRepository.findByIdForUpdate(1L)).willReturn(Optional.of(book));
        given(characterRelationRepository.existsByBookId(1L)).willReturn(true);
        given(chapterRepository.findAllByBookIdOrderByChapterNumber(1L)).willReturn(List.of(chapter));

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
```

- [ ] **Step 3: Run test to verify it fails**

```bash
mvn test -pl . -Dtest="NerResultProcessorTest"
```

Expected: FAIL — `incrementNerCompletedCount` is not called because old code uses `setNerCompletedCount` + `save`.

- [ ] **Step 4: Modify NerResultProcessor to use atomic increment**

Open `src/main/java/com/stokuj/books/integration/processor/NerResultProcessor.java`. Replace lines 50-51:

```java
        book.setNerCompletedCount(book.getNerCompletedCount() + 1);
        bookRepository.save(book);
```

With:

```java
        bookRepository.incrementNerCompletedCount(book.getId());
```

The full method after change:

```java
    @Transactional
    public void process(Chapter chapter, NerResult result) {
        chapter.setNerResult(result);
        chapterRepository.save(chapter);

        Book book = bookRepository.findByIdForUpdate(chapter.getBook().getId()).orElse(null);
        if (book == null) {
            return;
        }

        bookCharacterAggregator.applyNerResult(book, result);
        bookRepository.incrementNerCompletedCount(book.getId());

        int expectedCount = book.getNerCompletedCount() + 1;
        boolean readyForFindPairs = expectedCount >= book.getChaptersCount();
        if (!readyForFindPairs && chapter.getChapterNumber() == 1) {
            readyForFindPairs = true;
        }

        if (readyForFindPairs && !characterRelationRepository.existsByBookId(book.getId())) {
            Map<String, Integer> characterMap = bookCharacterAggregator.toCharacterMap(book.getId());
            if (characterMap.isEmpty()) {
                return;
            }
            List<Chapter> chapters = chapterRepository.findAllByBookIdOrderByChapterNumber(book.getId());
            String fullContent = chapters.stream()
                    .map(Chapter::getContent)
                    .collect(Collectors.joining("\n\n"));
            chapterEventProducer.sendBookForFindPairs(book.getId(), fullContent, characterMap);
        }
    }
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
mvn test -pl . -Dtest="NerResultProcessorTest"
```

Expected: PASS (all 5 tests)

- [ ] **Step 6: Commit**

```bash
git add src/main/java/com/stokuj/books/book/book/BookRepository.java src/main/java/com/stokuj/books/integration/processor/NerResultProcessor.java src/test/java/com/stokuj/books/integration/processor/NerResultProcessorTest.java
git commit -m "fix: use atomic DB increment for nerCompletedCount to prevent race condition"
```

---

### Task 2: Per-Relation Dedup

**Files:**
- Modify: `src/main/java/com/stokuj/books/integration/kafka/AnalysisResultConsumer.java`
- Modify: `src/main/java/com/stokuj/books/integration/processor/RelationsResultProcessor.java`
- Create: `src/test/java/com/stokuj/books/integration/processor/RelationsResultProcessorTest.java`

- [ ] **Step 1: Write failing test for RelationsResultProcessor per-relation dedup**

```bash
mvn test -pl . -Dtest="RelationsResultProcessorTest" -DfailIfNoTests=false
```

Expected: FAIL (no tests yet)

Create `src/test/java/com/stokuj/books/integration/processor/RelationsResultProcessorTest.java`:

```java
package com.stokuj.books.integration.processor;

import com.stokuj.books.integration.kafka.ChapterEventProducer;
import com.stokuj.books.book.book.Book;
import com.stokuj.books.book.character.core.StoryCharacter;
import com.stokuj.books.book.character.core.StoryCharacterService;
import com.stokuj.books.book.character.relation.StoryCharacterRelation;
import com.stokuj.books.book.character.relation.StoryCharacterRelationRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.lang.reflect.Field;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class RelationsResultProcessorTest {

    @Mock StoryCharacterRelationRepository characterRelationRepository;
    @Mock StoryCharacterService characterService;
    @Mock ChapterEventProducer chapterEventProducer;

    @InjectMocks RelationsResultProcessor processor;

    @Test
    void shouldSkipIndividualRelationThatAlreadyHasValue() {
        Book book = book(1L);
        StoryCharacter alice = character(10L, "Alice");
        StoryCharacter bob = character(20L, "Bob");
        StoryCharacter charlie = character(30L, "Charlie");

        StoryCharacterRelation existingRelation = new StoryCharacterRelation();
        existingRelation.setBook(book);
        existingRelation.setSource(alice);
        existingRelation.setTarget(bob);
        existingRelation.setRelation("friend");

        given(characterService.findOrCreate("Alice")).willReturn(alice);
        given(characterService.findOrCreate("Bob")).willReturn(bob);
        given(characterService.findOrCreate("Charlie")).willReturn(charlie);
        given(characterRelationRepository.findByBookIdAndSourceIdAndTargetId(1L, 10L, 20L))
                .willReturn(Optional.of(existingRelation));
        given(characterRelationRepository.findByBookIdAndSourceIdAndTargetId(1L, 10L, 30L))
                .willReturn(Optional.empty());

        Map<String, Object> result = Map.of("all_relations", List.of(
                Map.of("relations", Map.of("relations", List.of(
                        Map.of("source", "Alice", "target", "Bob", "relation", "enemy"),
                        Map.of("source", "Alice", "target", "Charlie", "relation", "ally")
                )))
        ));

        processor.processRelationsResult(book, result);

        ArgumentCaptor<StoryCharacterRelation> captor = ArgumentCaptor.forClass(StoryCharacterRelation.class);
        verify(characterRelationRepository).save(captor.capture());
        assertThat(captor.getValue().getRelation()).isEqualTo("ally");
    }

    @Test
    void shouldSkipIndividualRelationThatHasBlankValue() {
        Book book = book(1L);
        StoryCharacter alice = character(10L, "Alice");
        StoryCharacter bob = character(20L, "Bob");

        StoryCharacterRelation existingEmpty = new StoryCharacterRelation();
        existingEmpty.setBook(book);
        existingEmpty.setSource(alice);
        existingEmpty.setTarget(bob);
        existingEmpty.setRelation("  ");

        given(characterService.findOrCreate("Alice")).willReturn(alice);
        given(characterService.findOrCreate("Bob")).willReturn(bob);
        given(characterRelationRepository.findByBookIdAndSourceIdAndTargetId(1L, 10L, 20L))
                .willReturn(Optional.of(existingEmpty));

        Map<String, Object> result = Map.of("all_relations", List.of(
                Map.of("relations", Map.of("relations", List.of(
                        Map.of("source", "Alice", "target", "Bob", "relation", "friend")
                )))
        ));

        processor.processRelationsResult(book, result);

        verify(characterRelationRepository).save(any(StoryCharacterRelation.class));
    }

    private Book book(Long id) {
        Book book = new Book();
        setField(book, "id", id);
        return book;
    }

    private StoryCharacter character(Long id, String name) {
        StoryCharacter character = new StoryCharacter();
        setField(character, "id", id);
        setField(character, "name", name);
        return character;
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
mvn test -pl . -Dtest="RelationsResultProcessorTest"
```

Expected: FAIL — existing relation "friend" is overwritten with "enemy" because no per-relation skip exists yet.

- [ ] **Step 3: Modify RelationsResultProcessor to skip already-resolved relations**

Open `src/main/java/com/stokuj/books/integration/processor/RelationsResultProcessor.java`. In the `processRelationsResult` method, after finding the existing relation (line 92-100), add a skip check before the `setRelation` call:

Replace the existing `forEach` block inside the inner `innerList.stream()` (lines 81-105) — specifically add the skip check after `orElseGet`:

The changed section:

```java
                                    StoryCharacterRelation relation = characterRelationRepository
                                            .findByBookIdAndSourceIdAndTargetId(book.getId(), source.getId(), target.getId())
                                            .orElseGet(() -> {
                                                StoryCharacterRelation created = new StoryCharacterRelation();
                                                created.setBook(book);
                                                created.setSource(source);
                                                created.setTarget(target);
                                                return created;
                                            });
                                    if (relation.getRelation() != null && !relation.getRelation().isBlank()) {
                                        return;
                                    }
                                    relation.setRelation(blankToNull(asString(rel.get("relation"))));
                                    relation.setEvidence(blankToNull(asString(rel.get("evidence"))));
                                    relation.setConfidence(asDouble(rel.get("confidence")));
                                    characterRelationRepository.save(relation);
```

- [ ] **Step 4: Remove global pre-check from AnalysisResultConsumer**

Open `src/main/java/com/stokuj/books/integration/kafka/AnalysisResultConsumer.java`. Remove lines 140-146 (the `hasResolvedRelations` block).

Before (lines 140-148):
```java
        boolean hasResolvedRelations = characterRelationRepository.findAllByBookId(bookId)
                .stream()
                .anyMatch(rel -> rel.getRelation() != null && !rel.getRelation().isBlank());
        if (hasResolvedRelations) {
            log.info("Skipping duplicate relations result for book {}", bookId);
            return;
        }

        relationsResultProcessor.processRelationsResult(book, payload);
```

After:
```java
        relationsResultProcessor.processRelationsResult(book, payload);
```

- [ ] **Step 5: Run all tests to verify they pass**

```bash
mvn test -pl . -Dtest="RelationsResultProcessorTest,NerResultProcessorTest"
```

Expected: PASS (all tests)

- [ ] **Step 6: Commit**

```bash
git add src/main/java/com/stokuj/books/integration/kafka/AnalysisResultConsumer.java src/main/java/com/stokuj/books/integration/processor/RelationsResultProcessor.java src/test/java/com/stokuj/books/integration/processor/RelationsResultProcessorTest.java
git commit -m "fix: check relation dedup per-pair instead of globally skipping entire batches"
```

---

### Task 3: Missing Stats Field Validation

**Files:**
- Modify: `src/main/java/com/stokuj/books/integration/kafka/AnalysisResultConsumer.java`
- Create: `src/test/java/com/stokuj/books/integration/kafka/AnalysisResultConsumerTest.java`

- [ ] **Step 1: Write failing test for stats validation logging**

```bash
mvn test -pl . -Dtest="AnalysisResultConsumerTest" -DfailIfNoTests=false
```

Expected: FAIL (no tests yet)

Create `src/test/java/com/stokuj/books/integration/kafka/AnalysisResultConsumerTest.java`:

```java
package com.stokuj.books.integration.kafka;

import ch.qos.logback.classic.Level;
import ch.qos.logback.classic.Logger;
import ch.qos.logback.classic.spi.ILoggingEvent;
import ch.qos.logback.core.read.ListAppender;
import com.stokuj.books.integration.processor.NerResultProcessor;
import com.stokuj.books.integration.processor.RelationsResultProcessor;
import com.stokuj.books.book.book.Book;
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
import static org.mockito.ArgumentMatchers.any;
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
mvn test -pl . -Dtest="AnalysisResultConsumerTest"
```

Expected: The test `shouldLogWarningWhenStatsFieldsAreMissing` fails because no warning is logged yet.

- [ ] **Step 3: Add validation logging to AnalysisResultConsumer**

Open `src/main/java/com/stokuj/books/integration/kafka/AnalysisResultConsumer.java`. Replace lines 69-72:

```java
        chapter.setCharCount(asInt(analysis.get("char_count"), asInt(analysis.get("charCount"), null)));
        chapter.setCharCountClean(asInt(analysis.get("char_count_clean"), asInt(analysis.get("charCountClean"), null)));
        chapter.setWordCount(asInt(analysis.get("word_count"), asInt(analysis.get("wordCount"), null)));
        chapter.setTokenCount(asInt(analysis.get("token_count"), asInt(analysis.get("tokenCount"), null)));
```

With:

```java
        Integer charCount = asInt(analysis.get("char_count"), asInt(analysis.get("charCount"), null));
        Integer charCountClean = asInt(analysis.get("char_count_clean"), asInt(analysis.get("charCountClean"), null));
        Integer wordCount = asInt(analysis.get("word_count"), asInt(analysis.get("wordCount"), null));
        Integer tokenCount = asInt(analysis.get("token_count"), asInt(analysis.get("tokenCount"), null));

        if (charCount == null) log.warn("Missing char_count in analysis result for chapter {}", chapterId);
        if (charCountClean == null) log.warn("Missing char_count_clean in analysis result for chapter {}", chapterId);
        if (wordCount == null) log.warn("Missing word_count in analysis result for chapter {}", chapterId);
        if (tokenCount == null) log.warn("Missing token_count in analysis result for chapter {}", chapterId);

        chapter.setCharCount(charCount);
        chapter.setCharCountClean(charCountClean);
        chapter.setWordCount(wordCount);
        chapter.setTokenCount(tokenCount);
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
mvn test -pl . -Dtest="AnalysisResultConsumerTest"
```

Expected: PASS (all 3 tests)

- [ ] **Step 5: Verify no existing tests break**

```bash
mvn test -pl .
```

Expected: PASS (all tests)

- [ ] **Step 6: Commit**

```bash
git add src/main/java/com/stokuj/books/integration/kafka/AnalysisResultConsumer.java src/test/java/com/stokuj/books/integration/kafka/AnalysisResultConsumerTest.java
git commit -m "fix: log warnings when analysis stats fields are missing"
```

---

### Task 4: Explicit Kafka Serializer Type for PairResult

**Files:**
- Modify: `src/main/java/com/stokuj/books/integration/kafka/ChapterEventProducer.java`
- Create: `src/test/java/com/stokuj/books/integration/kafka/ChapterEventProducerTest.java`

- [ ] **Step 1: Write test for ChapterEventProducer**

```bash
mvn test -pl . -Dtest="ChapterEventProducerTest" -DfailIfNoTests=false
```

Expected: FAIL (no tests yet)

Create `src/test/java/com/stokuj/books/integration/kafka/ChapterEventProducerTest.java`:

```java
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

    @Mock KafkaTemplate<Object, Object> kafkaTemplate;

    @InjectMocks ChapterEventProducer producer;

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
```

- [ ] **Step 2: Run test to verify it fails initially (if not yet compiled with typed signature)**

```bash
mvn test -pl . -Dtest="ChapterEventProducerTest"
```

Expected: This may pass if the compilation still works, but it will confirm our typed change compiles correctly.

- [ ] **Step 3: Change method signature in ChapterEventProducer**

Open `src/main/java/com/stokuj/books/integration/kafka/ChapterEventProducer.java`. Add the import:

```java
import com.stokuj.books.integration.dto.PairResult;
```

Change the `sendBookForRelations` method signature (line 56):

```java
    public void sendBookForRelations(Long bookId, List<PairResult> pairs) {
```

(The `List<?>` becomes `List<PairResult>`)

- [ ] **Step 4: Run tests to verify they pass**

```bash
mvn test -pl . -Dtest="ChapterEventProducerTest"
```

Expected: PASS (both tests)

- [ ] **Step 5: Run full test suite**

```bash
mvn test -pl .
```

Expected: PASS (all tests)

- [ ] **Step 6: Commit**

```bash
git add src/main/java/com/stokuj/books/integration/kafka/ChapterEventProducer.java src/test/java/com/stokuj/books/integration/kafka/ChapterEventProducerTest.java
git commit -m "fix: use typed List<PairResult> instead of raw List<?> in Kafka producer"
```

---

### Task 5: Final Verification

- [ ] **Step 1: Run full test suite**

```bash
mvn test -pl .
```

Expected: PASS (all tests, no regressions)

- [ ] **Step 2: Compile check**

```bash
mvn compile -pl .
```

Expected: BUILD SUCCESS
