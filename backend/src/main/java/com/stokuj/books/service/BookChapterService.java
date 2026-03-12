package com.stokuj.books.service;

import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.model.Book;
import com.stokuj.books.model.BookChapter;
import com.stokuj.books.repository.BookChapterRepository;
import com.stokuj.books.repository.BookRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Service
public class BookChapterService {

    private final BookChapterRepository chapterRepository;
    private final BookRepository bookRepository;

    private static final int MIN_CHAPTER_SIZE = 1200;

    // regex dopasowujący słowne liczby ONE, TWENTY-ONE itd.
    private static final Pattern WORD_NUMBER_PATTERN = Pattern.compile(
            "(?i)^(?:one|two|three|four|five|six|seven|eight|nine|ten|"
                    + "eleven|twelve|thirteen|fourteen|fifteen|"
                    + "sixteen|seventeen|eighteen|nineteen|"
                    + "twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety"
                    + "(?:[- ](?:one|two|three|four|five|six|seven|eight|nine))?)$"
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
            String content = parts.get(i).strip();

            BookChapter chapter = new BookChapter();
            chapter.setBook(book);
            chapter.setChapterNumber(i + 1);
            chapter.setContent(content);

            String firstLine = content.lines().findFirst().orElse("");
            if (firstLine.length() > 150) {
                firstLine = firstLine.substring(0, 150);
            }
            chapter.setTitle(firstLine);

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
        String[] lines = text.split("\n");

        List<Integer> chapterLines = new ArrayList<>();
        for (int i = 0; i < lines.length; i++) {
            if (isChapterLine(lines[i])) {
                chapterLines.add(i);
            }
        }

        if (chapterLines.isEmpty()) {
            return List.of(text.strip());
        }

        List<String> chapters = new ArrayList<>();

        // preambuła przed pierwszym rozdziałem
        if (chapterLines.get(0) > 0) {
            String preamble = String.join("\n", Arrays.copyOfRange(lines, 0, chapterLines.get(0))).strip();
            if (!preamble.isBlank()) {
                chapters.add(preamble);
            }
        }

        for (int i = 0; i < chapterLines.size(); i++) {
            int start = chapterLines.get(i);
            int end = (i + 1 < chapterLines.size()) ? chapterLines.get(i + 1) : lines.length;

            String part = String.join("\n", Arrays.copyOfRange(lines, start, end)).strip();

            if (part.isBlank()) continue;

            if (part.length() < MIN_CHAPTER_SIZE && !chapters.isEmpty()) {
                // łączymy z poprzednim rozdziałem
                String merged = chapters.remove(chapters.size() - 1) + "\n\n" + part;
                chapters.add(merged);
            } else {
                chapters.add(part);
            }
        }

        return chapters;
    }

    private boolean isChapterLine(String line) {
        line = line.strip();
        if (line.isEmpty()) return false;

        int score = 0;
        String lower = line.toLowerCase();

        // keywords
        if (lower.startsWith("chapter")) score += 3;
        if (lower.startsWith("prologue") || lower.startsWith("epilogue")) score += 3;

        // linia CAPS (ONE, TWENTY-ONE)
        if (line.equals(line.toUpperCase()) && line.length() <= 25) score += 2;

        // linia krótka
        if (line.length() <= 60) score += 1;

        // słowna liczba
        if (WORD_NUMBER_PATTERN.matcher(line).matches()) score += 2;

        return score >= 3;
    }
}