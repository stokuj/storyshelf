package com.stokuj.books.service;

import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.model.Book;
import com.stokuj.books.model.BookChapter;
import com.stokuj.books.repository.BookChapterRepository;
import com.stokuj.books.repository.BookRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

@Service
public class BookChapterService {

    private final BookChapterRepository chapterRepository;
    private final BookRepository bookRepository;

    private static final Pattern CHAPTER_PATTERN = Pattern.compile(
            "^(chapter|rozdział|part|księga)\\s+[\\dIVXivx]+",
            Pattern.CASE_INSENSITIVE | Pattern.MULTILINE
    );

    public BookChapterService(BookChapterRepository chapterRepository,
                              BookRepository bookRepository) {
        this.chapterRepository = chapterRepository;
        this.bookRepository = bookRepository;
    }

    @Transactional
    public int loadContent(Long bookId, String fullText) {
        Book book = bookRepository.findById(bookId)
                .orElseThrow(() -> new ResourceNotFoundException("Book not found"));

        chapterRepository.deleteAllByBookId(bookId);

        List<String> parts = splitIntoChapters(fullText);

        List<BookChapter> chapters = new ArrayList<>();
        for (int i = 0; i < parts.size(); i++) {
            BookChapter chapter = new BookChapter();
            chapter.setBook(book);
            chapter.setChapterNumber(i + 1);
            chapter.setContent(parts.get(i).strip());
            chapters.add(chapter);
        }

        chapterRepository.saveAll(chapters);
        return chapters.size();
    }

    public List<BookChapter> getChapters(Long bookId) {
        return chapterRepository.findAllByBookIdOrderByChapterNumber(bookId);
    }

    @Transactional
    public void clearContent(Long bookId) {
        chapterRepository.deleteAllByBookId(bookId);
    }

    private List<String> splitIntoChapters(String text) {
        String[] parts = CHAPTER_PATTERN.split(text);

        if (parts.length <= 1) {
            return splitByWordCount(text, 10000);
        }

        return Arrays.stream(parts)
                .filter(s -> !s.isBlank())
                .toList();
    }

    private List<String> splitByWordCount(String text, int wordsPerChunk) {
        String[] words = text.split("\\s+");
        List<String> chunks = new ArrayList<>();

        for (int i = 0; i < words.length; i += wordsPerChunk) {
            int end = Math.min(i + wordsPerChunk, words.length);
            chunks.add(String.join(" ", Arrays.copyOfRange(words, i, end)));
        }

        return chunks;
    }
}