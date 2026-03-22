package com.stokuj.books.integration.processor;

import com.stokuj.books.dto.integration.NerResult;
import com.stokuj.books.repository.BookChapterRepository;
import com.stokuj.books.repository.BookRepository;
import com.stokuj.books.repository.CharacterRelationRepository;
import com.stokuj.books.integration.kafka.ChapterEventProducer;
import com.stokuj.books.service.BookCharacterAggregator;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Component
public class NerResultProcessor {

    private final BookChapterRepository chapterRepository;
    private final BookRepository bookRepository;
    private final CharacterRelationRepository characterRelationRepository;
    private final ChapterEventProducer chapterEventProducer;
    private final BookCharacterAggregator bookCharacterAggregator;

    public NerResultProcessor(BookChapterRepository chapterRepository,
                              BookRepository bookRepository,
                              CharacterRelationRepository characterRelationRepository,
                              ChapterEventProducer chapterEventProducer,
                              BookCharacterAggregator bookCharacterAggregator) {
        this.chapterRepository = chapterRepository;
        this.bookRepository = bookRepository;
        this.characterRelationRepository = characterRelationRepository;
        this.chapterEventProducer = chapterEventProducer;
        this.bookCharacterAggregator = bookCharacterAggregator;
    }

    @Transactional
    public void process(Chapter chapter, NerResult result) {
        chapter.setNerResult(result);
        chapterRepository.save(chapter);

        Book book = bookRepository.findByIdForUpdate(chapter.getBook().getId()).orElse(null);
        if (book == null) {
            return;
        }

        bookCharacterAggregator.applyNerResult(book, result);
        book.setNerCompletedCount(book.getNerCompletedCount() + 1);
        bookRepository.save(book);

        boolean readyForFindPairs = book.getNerCompletedCount() >= book.getChaptersCount();
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

    
}
