"""CLI entrypoint for StoryWeave."""

import logging
from pathlib import Path

from .book import Book
from .book_service import BookService
from .llm import LLMService
from .spacy_part import extract_characters_from_chapter as spacy_analysis
from .transformers_part import extract_characters_from_chapter as transformers_analysis


DEFAULT_BOOK_PATH = Path("old/books/hobbit.txt")


class StoryWeaveApplication:
    """Run the app flow: load book and save results."""

    def __init__(self) -> None:
        """Prepare app dependencies and state."""
        self._book = Book()
        self._book_service = BookService()
        self._llm_service = LLMService()

    def run(self) -> None:
        """Start the app flow."""

        # Init Part
        self._book = self._book_service.load_txt(str(DEFAULT_BOOK_PATH))
        self._book_service.analyze(self._book)

        # Model Part
        chapter_numbers = list(range(1, len(self._book.chapters) + 1))
        chapter_numbers = [1]

        # spacy_analysis(self._book, chapter_numbers, "en_core_web_sm")
        # spacy_analysis(self._book, chapter_numbers, "en_core_web_trf")
        # transformers_analysis(self._book, chapter_numbers, "dslim/bert-base-NER")
        # transformers_analysis(self._book,chapter_numbers,"dbmdz/bert-large-cased-finetuned-conll03-english",)

        # Pair sentences extraction
        pairs_data = self._book_service.find_pair_sentences(self._book, ["Gandalf", "Bilbo", "Thorin"])


        # LLM relation extraction — one call per character pair
        for entry in pairs_data:

            relations = self._llm_service.extract_relations(entry["pair"], entry["sentences"])
            logging.info("Relations for %s: %s", entry["pair"], relations)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    app = StoryWeaveApplication()
    app.run()
