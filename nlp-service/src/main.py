"""CLI entrypoint for StoryWeave."""

from .book import Book


class StoryWeaveApplication:
    """Run the app flow: load book and show stats."""

    def __init__(self):
        """Prepare app state."""
        self._book = Book()

    def run(self):
        """Start the app flow."""
        self._book = Book.read_txt("src/books/hobbit.txt")
        stats = self._book.stats()

        print(f"Characters: {stats['characters']}")
        print(f"Words: {stats['words']}")
        print(f"Sentences: {stats['sentences']}")
        print(f"Chapters: {stats['chapters']}")
        print(f"Average chapter length (words): {stats['avg_chapter_words']:.2f}")
        print(f"Average word length: {stats['avg_word_length']:.2f}")


if __name__ == "__main__":
    app = StoryWeaveApplication()
    app.run()
