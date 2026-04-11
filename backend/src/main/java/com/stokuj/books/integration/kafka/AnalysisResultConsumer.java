package com.stokuj.books.integration.kafka;

import com.stokuj.books.integration.dto.BookFindPairsResult;
import com.stokuj.books.integration.dto.NerResult;
import com.stokuj.books.integration.dto.PairResult;
import com.stokuj.books.integration.processor.NerResultProcessor;
import com.stokuj.books.integration.processor.RelationsResultProcessor;
import com.stokuj.books.book.book.Book;
import com.stokuj.books.book.book.BookRepository;
import com.stokuj.books.book.chapter.BookChapterRepository;
import com.stokuj.books.book.chapter.Chapter;
import com.stokuj.books.book.character.relation.StoryCharacterRelationRepository;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;
import java.util.Map;

@Component
public class AnalysisResultConsumer {

    private static final Logger log = LoggerFactory.getLogger(AnalysisResultConsumer.class);

    private final BookChapterRepository chapterRepository;
    private final BookRepository bookRepository;
    private final NerResultProcessor nerResultProcessor;
    private final RelationsResultProcessor relationsResultProcessor;
    private final StoryCharacterRelationRepository characterRelationRepository;

    public AnalysisResultConsumer(BookChapterRepository chapterRepository,
                                  BookRepository bookRepository,
                                  NerResultProcessor nerResultProcessor,
                                  RelationsResultProcessor relationsResultProcessor,
                                  StoryCharacterRelationRepository characterRelationRepository) {
        this.chapterRepository = chapterRepository;
        this.bookRepository = bookRepository;
        this.nerResultProcessor = nerResultProcessor;
        this.relationsResultProcessor = relationsResultProcessor;
        this.characterRelationRepository = characterRelationRepository;
    }

    @Transactional
    @KafkaListener(topics = "chapter.analyse.results", groupId = "springshelf-analysis-results")
    public void consumeAnalyseResult(Map<String, Object> payload) {
        Long chapterId = asLong(payload.get("chapterId"));
        if (chapterId == null) {
            log.warn("Invalid chapter.analyse.results payload, missing chapterId: {}", payload);
            return;
        }

        Chapter chapter = chapterRepository.findById(chapterId).orElse(null);
        if (chapter == null) {
            throw new IllegalStateException("Chapter not found for analyse result: " + chapterId);
        }
        if (Boolean.TRUE.equals(chapter.getAnalysisCompleted())) {
            log.info("Skipping duplicate analyse result for chapter {}", chapterId);
            return;
        }

        Map<String, Object> analysis = asMap(payload.get("analysis"));
        if (analysis == null) {
            log.warn("Invalid chapter.analyse.results payload, missing analysis: {}", payload);
            return;
        }

        chapter.setCharCount(asInt(analysis.get("char_count"), asInt(analysis.get("charCount"), null)));
        chapter.setCharCountClean(asInt(analysis.get("char_count_clean"), asInt(analysis.get("charCountClean"), null)));
        chapter.setWordCount(asInt(analysis.get("word_count"), asInt(analysis.get("wordCount"), null)));
        chapter.setTokenCount(asInt(analysis.get("token_count"), asInt(analysis.get("tokenCount"), null)));
        chapter.setAnalysisCompleted(true);
        chapterRepository.save(chapter);
    }

    @Transactional
    @KafkaListener(topics = "chapter.ner.results", groupId = "springshelf-analysis-results")
    public void consumeNerResult(Map<String, Object> payload) {
        Long chapterId = asLong(payload.get("chapterId"));
        if (chapterId == null) {
            log.warn("Invalid chapter.ner.results payload, missing chapterId: {}", payload);
            return;
        }

        Chapter chapter = chapterRepository.findById(chapterId).orElse(null);
        if (chapter == null) {
            throw new IllegalStateException("Chapter not found for ner result: " + chapterId);
        }
        if (chapter.getNerResult() != null) {
            log.info("Skipping duplicate NER result for chapter {}", chapterId);
            return;
        }

        Map<String, Object> nerPayload = asMap(payload.get("result"));
        if (nerPayload == null) {
            nerPayload = payload;
        }

        NerResult result = new NerResult();
        result.setCharacters(asStringIntMap(nerPayload.get("characters")));
        nerResultProcessor.process(chapter, result);
    }

    @Transactional
    @KafkaListener(topics = "book.find-pairs.results", groupId = "springshelf-analysis-results")
    public void consumeFindPairsResult(Map<String, Object> payload) {
        Long bookId = asLong(payload.get("bookId"));
        if (bookId == null) {
            log.warn("Invalid book.find-pairs.results payload, missing bookId: {}", payload);
            return;
        }

        Book book = bookRepository.findById(bookId).orElse(null);
        if (book == null) {
            throw new IllegalStateException("Book not found for find-pairs result: " + bookId);
        }
        if (characterRelationRepository.existsByBookId(bookId)) {
            log.info("Skipping duplicate find-pairs result for book {}", bookId);
            return;
        }

        BookFindPairsResult result = new BookFindPairsResult();
        result.setPairs(asPairResults(payload.get("pairs")));
        relationsResultProcessor.processFindPairsResult(book, result);
    }

    @Transactional
    @KafkaListener(topics = "book.relations.results", groupId = "springshelf-analysis-results")
    public void consumeRelationsResult(Map<String, Object> payload) {
        Long bookId = asLong(payload.get("bookId"));
        if (bookId == null) {
            log.warn("Invalid book.relations.results payload, missing bookId: {}", payload);
            return;
        }

        Book book = bookRepository.findById(bookId).orElse(null);
        if (book == null) {
            throw new IllegalStateException("Book not found for relations result: " + bookId);
        }

        boolean hasResolvedRelations = characterRelationRepository.findAllByBookId(bookId)
                .stream()
                .anyMatch(rel -> rel.getRelation() != null && !rel.getRelation().isBlank());
        if (hasResolvedRelations) {
            log.info("Skipping duplicate relations result for book {}", bookId);
            return;
        }

        relationsResultProcessor.processRelationsResult(book, payload);
    }

    private Long asLong(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof Number number) {
            return number.longValue();
        }
        try {
            return Long.parseLong(String.valueOf(value));
        } catch (NumberFormatException ignored) {
            return null;
        }
    }

    private Integer asInt(Object value, Integer fallback) {
        if (value == null) {
            return fallback;
        }
        if (value instanceof Number number) {
            return number.intValue();
        }
        try {
            return Integer.parseInt(String.valueOf(value));
        } catch (NumberFormatException ignored) {
            return fallback;
        }
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> asMap(Object value) {
        if (value instanceof Map<?, ?> map) {
            return (Map<String, Object>) map;
        }
        return null;
    }

    @SuppressWarnings("unchecked")
    private Map<String, Integer> asStringIntMap(Object value) {
        if (!(value instanceof Map<?, ?> raw)) {
            return Map.of();
        }
        return raw.entrySet().stream()
                .filter(e -> e.getKey() != null)
                .collect(java.util.stream.Collectors.toMap(
                        e -> String.valueOf(e.getKey()),
                        e -> asInt(e.getValue(), 0)
                ));
    }

    @SuppressWarnings("unchecked")
    private List<PairResult> asPairResults(Object value) {
        if (!(value instanceof List<?> rawList)) {
            return List.of();
        }
        return rawList.stream()
                .filter(item -> item instanceof Map<?, ?>)
                .map(item -> (Map<?, ?>) item)
                .map(item -> {
                    Object pairObj = item.get("pair");
                    if (!(pairObj instanceof List<?> pairRaw)) {
                        return null;
                    }
                    PairResult pairResult = new PairResult();
                    pairResult.setPair(pairRaw.stream().map(String::valueOf).toList());
                    return pairResult;
                })
                .filter(java.util.Objects::nonNull)
                .toList();
    }
}
