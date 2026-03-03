"""Book model and loading helpers."""

from __future__ import annotations

import re
from pathlib import Path


class Book:
    """Store book text and return basic text stats."""

    def __init__(self, text: str = ""):
        """Create a book object from raw text."""
        self.text = text

    @property
    def character_count(self) -> int:
        """Return number of characters in the text."""
        return len(self.text)

    @property
    def word_count(self) -> int:
        """Return number of words in the text."""
        return len(re.findall(r"\b\w+\b", self.text, flags=re.UNICODE))

    @property
    def chapter_count(self) -> int:
        """Return number of chapters detected in the text."""
        return len(self.chapter_texts())

    @property
    def sentence_count(self) -> int:
        """Return number of sentences in the text."""
        return len(
            [part for part in re.split(r"(?<=[.!?])\s+", self.text.strip()) if part]
        )

    @property
    def average_chapter_length(self) -> float:
        """Return average chapter length in words."""
        chapters = self.chapter_texts()
        if not chapters:
            return 0.0

        lengths = [
            len(re.findall(r"\b\w+\b", chapter, flags=re.UNICODE))
            for chapter in chapters
        ]
        return sum(lengths) / len(lengths)

    @property
    def average_word_length(self) -> float:
        """Return average word length in characters."""
        words = [
            word
            for word in re.findall(r"\b\w+\b", self.text, flags=re.UNICODE)
            if not word.isdigit()
        ]
        if not words:
            return 0.0

        return sum(len(word) for word in words) / len(words)

    def chapter_texts(self) -> list[str]:
        """Split text into chapters using chapter headings."""
        pattern = re.compile(r"(?im)^\s*(chapter|rozdzia[łl])\b.*$")
        matches = list(pattern.finditer(self.text))

        if not matches:
            return [self.text.strip()] if self.text.strip() else []

        chapters: list[str] = []
        for index, match in enumerate(matches):
            start = match.end()
            end = (
                matches[index + 1].start()
                if index + 1 < len(matches)
                else len(self.text)
            )
            content = self.text[start:end].strip()
            if content:
                chapters.append(content)

        return chapters

    def stats(self) -> dict[str, int | float]:
        """Return all basic stats in one dictionary."""
        return {
            "characters": self.character_count,
            "words": self.word_count,
            "sentences": self.sentence_count,
            "chapters": self.chapter_count,
            "avg_chapter_words": self.average_chapter_length,
            "avg_word_length": self.average_word_length,
        }

    @classmethod
    def read_txt(cls, file_name: str) -> "Book":
        """Load a TXT file and return a Book object."""
        file_path = Path(file_name)

        with file_path.open("r", encoding="utf-8") as file:
            return cls(file.read())
