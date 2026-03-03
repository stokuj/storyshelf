"""CLI entrypoint for StoryWeave."""

import logging

from .book import Book
from .book_service import BookService
from .spacy_part import extract_characters_from_chapter


class StoryWeaveApplication:
    """Run the app flow: load book and show stats."""

    def __init__(self):
        """Prepare app dependencies and state."""
        self._book = Book()
        self._book_service = BookService()

    def print_stats(self):
        """Print the stats about the book"""
        print(f"Characters: {self._book.character_count}")
        print(f"Words: {self._book.word_count}")
        print(f"Sentences: {self._book.sentence_count}")
        print(f"Chapters: {self._book.chapter_count}")
        print(f"Average chapter length (words): {self._book.average_chapter_words:.2f}")
        print(f"Average word length: {self._book.average_word_length:.2f}")

    def spacy_analysis(self, chapter_number: int, model_name: str):
        """Analyze the characters in the chapter using spaCy."""

        try:
            chapter_characters = extract_characters_from_chapter(
                self._book.text,
                chapter_number,
                model_name,
            )
        except RuntimeError as error:
            logging.warning("Skipping model %s: %s", model_name, error)
            return

        print(
            f"Characters in chapter {chapter_number} "
            f"(spaCy PERSON, model={model_name}):"
        )
        if not chapter_characters:
            print("No PERSON entities found.")
            return

        for name, count in chapter_characters.items():
            print(f"- {name}: {count}")

    def run(self):
        """Start the app flow."""
        self._book = self._book_service.load_txt("src/books/hobbit.txt")
        self._book_service.analyze(self._book)

        ### SPACY
        # Spacy: Chapter Number, Model Name
        # self.spacy_analysis(1, "en_core_web_sm")
        # self.spacy_analysis(1, "en_core_web_trf")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    app = StoryWeaveApplication()
    app.run()
