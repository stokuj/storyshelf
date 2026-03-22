package com.stokuj.books.service;

import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.domain.entity.Book;
import com.stokuj.books.domain.entity.Chapter;
import com.stokuj.books.repository.BookCharacterRepository;
import com.stokuj.books.repository.BookChapterRepository;
import com.stokuj.books.repository.BookRepository;
import com.stokuj.books.repository.CharacterRelationRepository;
import com.stokuj.books.integration.kafka.ChapterEventProducer;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Slf4j
@Service
public class BookChapterService {

    private final BookChapterRepository chapterRepository;
    private final BookRepository bookRepository;
    private final BookCharacterRepository bookCharacterRepository;
    private final CharacterRelationRepository characterRelationRepository;
    private final ChapterEventProducer chapterEventProducer;

    private static final int MIN_CHAPTER_SIZE = 2000;    // minimalny rozmiar fragmentu
    private static final int MAX_CHAPTER_SIZE = 50000;   // maksymalny rozmiar fragmentu

    // dopasowuje nagłówki: Chapter, Book, Prologue, Epilogue + liczby (arabic, roman, słowne)
    private static final Pattern CHAPTER_PATTERN = Pattern.compile(
            "(?i)^(?:chapter|book|prologue|epilogue)\\s+(?:\\d+|[ivxlcdm]+|" +
                    "one|two|three|four|five|six|seven|eight|nine|ten|" +
                    "eleven|twelve|thirteen|fourteen|fifteen|" +
                    "sixteen|seventeen|eighteen|nineteen|" +
                    "twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety" +
                    "(?:[- ](?:one|two|three|four|five|six|seven|eight|nine))?)" +
                    ".*$"
    );

    public BookChapterService(BookChapterRepository chapterRepository,
                              BookRepository bookRepository,
                              BookCharacterRepository bookCharacterRepository,
                              CharacterRelationRepository characterRelationRepository,
                              ChapterEventProducer chapterEventProducer) {
        this.chapterRepository = chapterRepository;
        this.bookRepository = bookRepository;
        this.bookCharacterRepository = bookCharacterRepository;
        this.characterRelationRepository = characterRelationRepository;
        this.chapterEventProducer = chapterEventProducer;
    }

    @Transactional
    public int loadContent(Long bookId, String fullText) {

        Book book = bookRepository.findById(bookId)
                .orElseThrow(() -> new ResourceNotFoundException("Book not found"));

        chapterRepository.deleteAllByBookId(bookId);

        List<String> parts = splitIntoChapters(fullText);
        List<Chapter> chapters = new ArrayList<>();
        int chapterNumber = 1;

        for (String part : parts) {
            List<String> subParts = splitLargeChapter(part);
            for (int i = 0; i < subParts.size(); i++) {
                String subPart = subParts.get(i).strip();

                if (subPart.isBlank()) continue;

                Chapter chapter = new Chapter();
                chapter.setBook(book);
                chapter.setChapterNumber(chapterNumber++);
                chapter.setContent(subPart);

                // tytuł = pierwsza linia oryginalnego rozdziału
                String firstLine = part.lines().findFirst().orElse("");
                if (firstLine.length() > 150) firstLine = firstLine.substring(0, 150);

                if (subParts.size() > 1) {
                    firstLine += " (Part " + (i + 1) + ")";
                }

                chapter.setTitle(firstLine);
                chapters.add(chapter);
            }
        }

        chapterRepository.saveAll(chapters);

        int count = chapterRepository.countByBookId(bookId);
        book.setChaptersCount(count);
        book.setNerCompletedCount(0);
        bookRepository.save(book);

        bookCharacterRepository.deleteAllByBookId(bookId);
        characterRelationRepository.deleteAllByBookId(bookId);

        for (Chapter chapter : chapters) {
            chapterEventProducer.sendChapterForAnalysis(chapter.getId(), chapter.getContent());
        }

        for (Chapter chapter : chapters) {
            if (chapter.getChapterNumber() == 1) {
                chapterEventProducer.sendChapterForNer(chapter.getId(), chapter.getContent());
            }
        }

        return chapters.size();
    }

    public List<Chapter> getChapters(Long bookId) {
        return chapterRepository.findAllByBookIdOrderByChapterNumber(bookId);
    }

    @Transactional
    public void clearContent(Long bookId) {
        chapterRepository.deleteAllByBookId(bookId);
    }

    // dzieli tekst na fragmenty według nagłówków
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

        // preambuła przed pierwszym nagłówkiem
        if (chapterLines.getFirst() > 0) {
            String preamble = String.join("\n", Arrays.copyOfRange(lines, 0, chapterLines.getFirst())).strip();
            if (!preamble.isBlank()) {
                chapters.add(preamble);
            }
        }

        for (int i = 0; i < chapterLines.size(); i++) {
            int start = chapterLines.get(i);
            int end = (i + 1 < chapterLines.size()) ? chapterLines.get(i + 1) : lines.length;

            String part = String.join("\n", Arrays.copyOfRange(lines, start, end)).strip();
            if (part.isBlank()) continue;

            // łącz krótkie fragmenty z poprzednim
            if (part.length() < MIN_CHAPTER_SIZE && !chapters.isEmpty()) {
                String merged = chapters.removeLast() + "\n\n" + part;
                chapters.add(merged);
            } else {
                chapters.add(part);
            }
        }

        return chapters;
    }

    // sprawdza, czy linia jest nagłówkiem rozdziału
    private boolean isChapterLine(String line) {
        line = line.strip();
        if (line.isEmpty()) return false;
        Matcher matcher = CHAPTER_PATTERN.matcher(line);
        return matcher.matches();
    }

    // dzieli duży rozdział na fragmenty po paragrafach
    private List<String> splitLargeChapter(String chapterContent) {
        List<String> parts = new ArrayList<>();
        if (chapterContent.length() <= MAX_CHAPTER_SIZE) {
            parts.add(chapterContent);
            return parts;
        }

        String[] paragraphs = chapterContent.split("\\n\\n");
        StringBuilder current = new StringBuilder();

        for (String para : paragraphs) {
            if (current.length() + para.length() + 2 > MAX_CHAPTER_SIZE) {
                if (!current.isEmpty()) parts.add(current.toString().strip());
                current = new StringBuilder();
            }
            if (!current.isEmpty()) current.append("\n\n");
            current.append(para);
        }

        if (!current.isEmpty()) parts.add(current.toString().strip());
        return parts;
    }
}
