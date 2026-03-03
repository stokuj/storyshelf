"""CLI entrypoint for StoryWeave."""

from .book import Book


class StoryWeaveApplication:
    def __init__(self):
        self._book = Book()

    def run(self):
        self._book = Book.read_txt("src/books/hobbit.txt")
        stats = self._book.stats()

        print(f"Characters: {stats['characters']}")
        print(f"Words: {stats['words']}")
        print(f"Sentences: {stats['sentences']}")


if __name__ == "__main__":
    app = StoryWeaveApplication()
    app.run()
