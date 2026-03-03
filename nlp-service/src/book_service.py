"""Services for loading and analyzing books."""

from __future__ import annotations

from pathlib import Path
import re

from .book import Book


class BookService:
    """Load books and calculate book statistics."""

    def load_txt(self, file_name: str) -> Book:
        """Load a TXT file and return a Book object."""
        file_path = Path(file_name)
        with file_path.open("r", encoding="utf-8") as file:
            text = file.read()
        return Book(
            text=text, source_path=str(file_path), chapters=self._split_chapters(text)
        )

    def _split_chapters(self, text: str) -> list[str]:
        """Split text into chapter blocks using chapter headings."""
        pattern = re.compile(r"(?im)^\s*(chapter|rozdzia[łl])\b.*$")
        matches = list(pattern.finditer(text))
        if not matches:
            return [text.strip()] if text.strip() else []

        chapters: list[str] = []
        for index, match in enumerate(matches):
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            content = text[start:end].strip()
            if content:
                chapters.append(content)
        return chapters

    def chapter_texts(self, book: Book) -> list[str]:
        """Return chapter list stored on the Book model."""
        if not book.chapters:
            book.chapters = self._split_chapters(book.text)
        return book.chapters

    def analyze(self, book: Book) -> Book:
        """Calculate stats and save them on the Book fields."""
        words = re.findall(r"\b\w+\b", book.text, flags=re.UNICODE)
        non_digit_words = [word for word in words if not word.isdigit()]
        sentences = [
            part for part in re.split(r"(?<=[.!?])\s+", book.text.strip()) if part
        ]

        chapters = self.chapter_texts(book)
        chapter_lengths = [
            len(re.findall(r"\b\w+\b", chapter, flags=re.UNICODE))
            for chapter in chapters
        ]
        avg_chapter_words = (
            sum(chapter_lengths) / len(chapter_lengths) if chapter_lengths else 0.0
        )
        avg_word_length = (
            sum(len(word) for word in non_digit_words) / len(non_digit_words)
            if non_digit_words
            else 0.0
        )

        book.character_count = len(book.text)
        book.word_count = len(words)
        book.sentence_count = len(sentences)
        book.chapter_count = len(chapters)
        book.average_chapter_words = avg_chapter_words
        book.average_word_length = avg_word_length
        return book
