"""CLI entrypoint for StoryWeave."""

from .book import Book
from .book_service import BookService


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


    def run(self):
        """Start the app flow."""
        self._book = self._book_service.load_txt("src/books/hobbit.txt")
        self._book_service.analyze(self._book)
        self.print_stats()

if __name__ == "__main__":
    app = StoryWeaveApplication()
    app.run()
