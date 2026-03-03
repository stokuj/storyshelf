"""Book data model."""

from dataclasses import dataclass, field


@dataclass(slots=True)
class Book:
    """Store book text and calculated statistics."""

    text: str = ""
    source_path: str = ""
    chapters: list[str] = field(default_factory=list)

    # NER results: {chapter_number: {character_name: count}}
    chapters_characters: dict[int, dict[str, int]] = field(default_factory=dict)

    # Count part
    character_count: int = 0
    word_count: int = 0
    sentence_count: int = 0
    chapter_count: int = 0

    # Average part
    average_chapter_words: float = 0.0
    average_word_length: float = 0.0
