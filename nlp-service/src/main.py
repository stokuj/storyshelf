"""CLI entrypoint for StoryWeave."""

import json
import logging
from pathlib import Path

from .book import Book
from .book_service import BookService
from .spacy_part import extract_characters_from_chapter


RESULTS_DIR = Path("results")


class StoryWeaveApplication:
    """Run the app flow: load book and show stats."""

    def __init__(self):
        """Prepare app dependencies and state."""
        self._book = Book()
        self._book_service = BookService()

    def _results_path(self, chapter_number: int, model_name: str) -> Path:
        """Build output path for one model/chapter result."""
        return RESULTS_DIR / f"chapter_{chapter_number}_{model_name}.json"

    def _save_result(self, result: dict) -> None:
        """Save one analysis result as JSON in results directory."""
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        output_path = self._results_path(
            chapter_number=result["chapter_number"],
            model_name=result["model_name"],
        )
        output_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logging.info("Saved result: %s", output_path)

    def spacy_analysis(self, chapter_number: int, model_name: str):
        """Analyze the characters in the chapter using spaCy."""

        try:
            result = extract_characters_from_chapter(
                self._book,
                chapter_number,
                model_name,
            )
        except RuntimeError as error:
            logging.warning("Skipping model %s: %s", model_name, error)
            return
        self._save_result(result)

    def run(self):
        """Start the app flow."""
        self._book = self._book_service.load_txt("src/books/hobbit.txt")
        self._book_service.analyze(self._book)

        self.spacy_analysis(1, "en_core_web_sm")
        #self.spacy_analysis(1, "en_core_web_trf")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    app = StoryWeaveApplication()
    app.run()
