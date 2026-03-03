"""Book data model."""

from dataclasses import dataclass


@dataclass(slots=True)
class Book:
    """Store book text and calculated statistics."""

    text: str = ""
    source_path: str = ""
    character_count: int = 0
    word_count: int = 0
    sentence_count: int = 0
    chapter_count: int = 0
    average_chapter_words: float = 0.0
    average_word_length: float = 0.0
