"""CLI entrypoint for StoryWeave."""

import json
import logging
from pathlib import Path

from .book import Book
from .book_service import BookService
from .spacy_part import extract_characters_from_chapter
from .transformers_part import (
    extract_characters_from_chapter as extract_characters_transformers,
)


DEFAULT_RESULTS_DIR = Path("results")
DEFAULT_BOOK_PATH = Path("src/books/hobbit.txt")


class StoryWeaveApplication:
    """Run the app flow: load book and save results."""

    def __init__(
        self,
        book_path: Path = DEFAULT_BOOK_PATH,
        results_dir: Path = DEFAULT_RESULTS_DIR,
    ) -> None:
        """Prepare app dependencies and state."""
        self._book = Book()
        self._book_service = BookService()
        self._book_path = book_path
        self._results_dir = results_dir

    def _save_result(self, result: dict) -> None:
        """Save one analysis result as JSON in results directory."""

        self._results_dir.mkdir(parents=True, exist_ok=True)
        safe_model_name = result["model_name"].replace("/", "_").replace(":", "_")
        output_path = self._results_dir / (
            f"chapter_{result['chapter_number']}_{result['engine']}_{safe_model_name}.json"
        )
        output_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        logging.info("Saved result: %s", output_path)

    def spacy_analysis(self, chapter_numbers: list[int], model_name: str) -> None:
        """Analyze the characters in one or many chapters using spaCy."""

        try:
            results = extract_characters_from_chapter(
                self._book, chapter_numbers, model_name
            )

        except (RuntimeError, ValueError) as error:
            logging.warning("Skipping model %s: %s", model_name, error)
            return

        for result in results:
            self._save_result(result)

    def transformers_analysis(
        self, chapter_numbers: list[int], model_name: str
    ) -> None:
        """Analyze the characters in one or many chapters using transformers."""

        try:
            results = extract_characters_transformers(
                self._book, chapter_numbers, model_name
            )

        except (RuntimeError, ValueError) as error:
            logging.warning("Skipping model %s: %s", model_name, error)
            return

        for result in results:
            self._save_result(result)

    def run(self) -> None:
        """Start the app flow."""

        # Init Part
        self._book = self._book_service.load_txt(str(self._book_path))
        self._book_service.analyze(self._book)

        # Model Part
        chapter_numbers = [1]
        # self.spacy_analysis(chapter_numbers, "en_core_web_sm")
        self.spacy_analysis(chapter_numbers, "en_core_web_trf")
        # self.transformers_analysis(chapter_numbers, "dslim/bert-base-NER")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    app = StoryWeaveApplication()
    app.run()
