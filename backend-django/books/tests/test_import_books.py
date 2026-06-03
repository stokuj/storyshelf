import json
import tempfile
from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import CommandError, call_command
from django.test import SimpleTestCase, TestCase

from books.management.commands.import_books import (
    _fetch_volume_info,
    _map_volume_info,
    _strip_html,
)
from books.models import Book, BookAuthor, BookGenre, BookTag
from library.models import Author, Genre, Tag


class StripHtmlTests(SimpleTestCase):
    def test_removes_tags_and_strips(self):
        self.assertEqual(_strip_html("<p>Hello <b>world</b></p>"), "Hello world")


class MapVolumeInfoTests(SimpleTestCase):
    def test_full_volume_maps_all_fields(self):
        volume = {
            "title": "Dune",
            "authors": ["Frank Herbert"],
            "publishedDate": "1965-08-01",
            "description": "<p>Epic SF</p>",
            "pageCount": 412,
            "imageLinks": {"thumbnail": "http://books.example/cover.jpg"},
            "categories": ["Fiction / Science Fiction / Epic"],
        }
        result = _map_volume_info(volume, "9780441013593")
        self.assertEqual(result["isbn"], "9780441013593")
        self.assertEqual(result["title"], "Dune")
        self.assertEqual(result["authors"], ["Frank Herbert"])
        self.assertEqual(result["year"], 1965)
        self.assertEqual(result["description"], "Epic SF")
        self.assertEqual(result["page_count"], 412)
        self.assertEqual(result["cover_url"], "https://books.example/cover.jpg")
        self.assertEqual(result["genres"], ["Fiction", "Science Fiction", "Epic"])
        self.assertNotIn("tags", result)

    def test_categories_split_and_deduped(self):
        volume = {
            "title": "X",
            "categories": ["Fiction / Fantasy", "Fiction / Adventure"],
        }
        result = _map_volume_info(volume, "111")
        self.assertEqual(result["genres"], ["Fiction", "Fantasy", "Adventure"])

    def test_missing_optional_fields_omitted(self):
        result = _map_volume_info({"title": "Bare"}, "222")
        self.assertEqual(result["title"], "Bare")
        self.assertEqual(result["isbn"], "222")
        absent_fields = (
            "year", "description", "page_count", "cover_url", "authors", "genres", "tags",
        )
        for absent in absent_fields:
            self.assertNotIn(absent, result)

    def test_year_parsed_from_year_only_date(self):
        result = _map_volume_info({"title": "X", "publishedDate": "1999"}, "333")
        self.assertEqual(result["year"], 1999)

    def test_zero_page_count_omitted(self):
        result = _map_volume_info({"title": "X", "pageCount": 0}, "444")
        self.assertNotIn("page_count", result)


def _fake_urlopen(payload):
    """Return a context-manager mock whose .read() yields payload as JSON bytes."""
    body = json.dumps(payload).encode("utf-8")
    cm = MagicMock()
    cm.__enter__.return_value.read.return_value = body
    cm.__exit__.return_value = False
    return cm


class FetchVolumeInfoTests(SimpleTestCase):
    @patch("books.management.commands.import_books.urllib.request.urlopen")
    def test_returns_first_volume_info(self, mock_urlopen):
        mock_urlopen.return_value = _fake_urlopen(
            {"totalItems": 1, "items": [{"volumeInfo": {"title": "Dune"}}]}
        )
        result = _fetch_volume_info("9780441013593", "")
        self.assertEqual(result, {"title": "Dune"})

    @patch("books.management.commands.import_books.urllib.request.urlopen")
    def test_no_items_returns_none(self, mock_urlopen):
        mock_urlopen.return_value = _fake_urlopen({"totalItems": 0})
        self.assertIsNone(_fetch_volume_info("000", ""))

    @patch("books.management.commands.import_books.urllib.request.urlopen")
    def test_api_key_appended_to_url(self, mock_urlopen):
        mock_urlopen.return_value = _fake_urlopen({"items": [{"volumeInfo": {}}]})
        _fetch_volume_info("123", "SECRET")
        called_url = mock_urlopen.call_args[0][0]
        self.assertIn("key=SECRET", called_url)
        self.assertIn("q=isbn%3A123", called_url)


_DUNE = {
    "items": [
        {
            "volumeInfo": {
                "title": "Dune",
                "authors": ["Frank Herbert"],
                "publishedDate": "1965",
                "description": "Epic SF",
                "pageCount": 412,
                "imageLinks": {"thumbnail": "http://books.example.com/c.jpg"},
                "categories": ["Fiction / Science Fiction"],
                "averageRating": 4.5,
                "ratingsCount": 1000,
            }
        }
    ]
}


class ImportBooksCommandTests(TestCase):
    @patch("books.management.commands.import_books.urllib.request.urlopen")
    def test_creates_new_book(self, mock_urlopen):
        mock_urlopen.return_value = _fake_urlopen(_DUNE)
        call_command("import_books", "9780441013593", stdout=StringIO())
        book = Book.objects.get(isbn="9780441013593")
        self.assertEqual(book.title, "Dune")
        self.assertEqual(book.year, 1965)
        self.assertEqual(book.page_count, 412)
        self.assertEqual(book.cover_url, "https://books.example.com/c.jpg")
        # BookWriteSerializer normalizes genre names to lowercase (existing
        # catalog write-path convention via _resolve_m2m).
        self.assertEqual(
            sorted(book.genres.values_list("name", flat=True)),
            ["fiction", "science fiction"],
        )
        self.assertEqual(book.avg_rating, 0.0)
        self.assertEqual(book.ratings_count, 0)

    @patch("books.management.commands.import_books.urllib.request.urlopen")
    def test_updates_existing_book_by_isbn(self, mock_urlopen):
        Book.objects.create(title="Old Title", isbn="9780441013593")
        mock_urlopen.return_value = _fake_urlopen(_DUNE)
        call_command("import_books", "9780441013593", stdout=StringIO())
        self.assertEqual(Book.objects.filter(isbn="9780441013593").count(), 1)
        self.assertEqual(Book.objects.get(isbn="9780441013593").title, "Dune")

    @patch("books.management.commands.import_books.urllib.request.urlopen")
    def test_not_found_creates_nothing(self, mock_urlopen):
        mock_urlopen.return_value = _fake_urlopen({"totalItems": 0})
        call_command("import_books", "000", stdout=StringIO())
        self.assertEqual(Book.objects.count(), 0)

    @patch("books.management.commands.import_books.urllib.request.urlopen")
    def test_dry_run_saves_nothing(self, mock_urlopen):
        mock_urlopen.return_value = _fake_urlopen(_DUNE)
        call_command("import_books", "9780441013593", "--dry-run", stdout=StringIO())
        self.assertEqual(Book.objects.count(), 0)

    @patch("books.management.commands.import_books.urllib.request.urlopen")
    def test_file_input(self, mock_urlopen):
        mock_urlopen.return_value = _fake_urlopen(_DUNE)
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
            fh.write("# comment\n\n9780441013593\n")
            path = fh.name
        call_command("import_books", "--file", path, stdout=StringIO())
        self.assertEqual(Book.objects.count(), 1)

    @patch("books.management.commands.import_books.urllib.request.urlopen")
    def test_update_preserves_existing_tags(self, mock_urlopen):
        book = Book.objects.create(title="Old Title", isbn="9780441013593")
        tag = Tag.objects.create(name="favourite")
        BookTag.objects.create(book=book, tag=tag)
        mock_urlopen.return_value = _fake_urlopen(_DUNE)
        call_command("import_books", "9780441013593", stdout=StringIO())
        book.refresh_from_db()
        self.assertEqual(list(book.tags.values_list("name", flat=True)), ["favourite"])

    @patch("books.management.commands.import_books.urllib.request.urlopen")
    def test_update_preserves_authors_genres_when_google_omits_them(self, mock_urlopen):
        book = Book.objects.create(title="Old Title", isbn="9780441013593")
        BookAuthor.objects.create(book=book, author=Author.objects.create(name="Frank Herbert"))
        BookGenre.objects.create(book=book, genre=Genre.objects.create(name="science fiction"))
        # Google returns the volume but without authors and without categories.
        payload = {"items": [{"volumeInfo": {"title": "Dune", "pageCount": 412}}]}
        mock_urlopen.return_value = _fake_urlopen(payload)
        call_command("import_books", "9780441013593", stdout=StringIO())
        book.refresh_from_db()
        self.assertEqual(book.title, "Dune")
        self.assertEqual(list(book.authors.values_list("name", flat=True)), ["Frank Herbert"])
        self.assertEqual(list(book.genres.values_list("name", flat=True)), ["science fiction"])

    @patch("books.management.commands.import_books.urllib.request.urlopen")
    def test_fetch_failure_exits_nonzero(self, mock_urlopen):
        mock_urlopen.side_effect = OSError("boom")
        with self.assertRaises(SystemExit) as ctx:
            call_command("import_books", "123", stdout=StringIO(), stderr=StringIO())
        self.assertEqual(ctx.exception.code, 1)
        self.assertEqual(Book.objects.count(), 0)

    def test_no_isbn_raises(self):
        with self.assertRaises(CommandError):
            call_command("import_books", stdout=StringIO())
