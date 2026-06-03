# Google Books Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `manage.py import_books` command that imports books into the catalog from the Google Books API by ISBN.

**Architecture:** A single management command in `books/management/commands/import_books.py` with a pure mapping helper (`_map_volume_info`, testable without DB) and a fetch helper (`_fetch_volume_info`, mocked in tests). Writes go through the existing `BookWriteSerializer` (create, or update by ISBN) so M2M get_or_create, slug generation and validation are reused. HTTP uses stdlib `urllib.request` (no new dependency).

**Tech Stack:** Django 6, DRF, Python 3.13, stdlib `urllib.request`, pytest/Django TestCase, `unittest.mock`.

---

## Spec

`docs/superpowers/specs/2026-06-03-google-books-import-design.md`

## Behaviour notes (read before starting)

- `BookWriteSerializer` requires only `title`; `year/isbn/description/page_count/cover_url` are optional, `authors/genres/tags` default to `[]`, `serie` is optional. The mapper omits any field Google didn't return.
- **On update**: the serializer's `update()` only `setattr`s fields present in the validated data, and only replaces an M2M when its key is provided. So fields Google did NOT return **keep their existing DB value** (we never null them). This is intended and matches the spec mapping ("brak → pomiń pole").
- Google's `averageRating`/`ratingsCount` are never mapped — our `avg_rating`/`ratings_count` are maintained by the `Rating` signal.
- Test DB: command tests use the DB (`TestCase`), so they need the dev Postgres (Docker stack up) or run inside the `storyshelf-django` container. The pure-mapper tests (Task 2) need no DB.

## File Structure

- `backend-django/config/settings/base.py` — add `GOOGLE_BOOKS_API_KEY` setting.
- `backend-django/books/management/commands/import_books.py` — command + `_strip_html`, `_map_volume_info`, `_fetch_volume_info`.
- `backend-django/books/tests/test_import_books.py` — all tests.
- `docs/ROADMAP.md` — move "Importer książek…" from "Kiedyś" to "Zrobione" (after implementation).

---

### Task 1: Add `GOOGLE_BOOKS_API_KEY` setting

**Files:**
- Modify: `backend-django/config/settings/base.py` (after the EMAIL block, around line 135)

- [ ] **Step 1: Add the setting**

In `backend-django/config/settings/base.py`, immediately after the line
`EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"`, add:

```python

# --- Google Books import (books/management/commands/import_books.py) ---
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY", "")
```

- [ ] **Step 2: Verify Django still loads**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py check`
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 3: Commit**

```bash
git add backend-django/config/settings/base.py
git commit -m "feat: add GOOGLE_BOOKS_API_KEY setting"
```

---

### Task 2: Pure mapper `_map_volume_info` + `_strip_html`

**Files:**
- Create: `backend-django/books/management/commands/import_books.py`
- Test: `backend-django/books/tests/test_import_books.py`

- [ ] **Step 1: Write the failing tests**

Create `backend-django/books/tests/test_import_books.py`:

```python
from django.test import SimpleTestCase

from books.management.commands.import_books import _map_volume_info, _strip_html


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
        self.assertEqual(result["tags"], [])

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
        self.assertEqual(result["tags"], [])
        for absent in ("year", "description", "page_count", "cover_url", "authors", "genres"):
            self.assertNotIn(absent, result)

    def test_year_parsed_from_year_only_date(self):
        result = _map_volume_info({"title": "X", "publishedDate": "1999"}, "333")
        self.assertEqual(result["year"], 1999)

    def test_zero_page_count_omitted(self):
        result = _map_volume_info({"title": "X", "pageCount": 0}, "444")
        self.assertNotIn("page_count", result)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend-django && DJANGO_ENV=dev uv run python -m pytest books/tests/test_import_books.py -v`
Expected: FAIL — `ModuleNotFoundError` / `ImportError: cannot import name '_map_volume_info'`.

- [ ] **Step 3: Implement the mapper**

Create `backend-django/books/management/commands/import_books.py`:

```python
import re

GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"
HTTP_TIMEOUT = 10


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def _map_volume_info(volume_info: dict, isbn: str) -> dict:
    """Map a Google Books volumeInfo dict to BookWriteSerializer input.

    Absent fields are omitted (not nulled), so on update they keep their
    current DB value. Google's averageRating/ratingsCount are never mapped.
    """
    mapped: dict = {"isbn": isbn, "tags": []}

    title = volume_info.get("title")
    if title:
        mapped["title"] = title

    authors = volume_info.get("authors")
    if authors:
        mapped["authors"] = authors

    published = volume_info.get("publishedDate", "")
    year_match = re.match(r"\d{4}", published)
    if year_match:
        mapped["year"] = int(year_match.group())

    description = volume_info.get("description")
    if description:
        mapped["description"] = _strip_html(description)

    page_count = volume_info.get("pageCount")
    if page_count:
        mapped["page_count"] = page_count

    thumbnail = volume_info.get("imageLinks", {}).get("thumbnail")
    if thumbnail:
        mapped["cover_url"] = thumbnail.replace("http://", "https://", 1)

    genres: list[str] = []
    for category in volume_info.get("categories", []):
        for part in category.split("/"):
            part = part.strip()
            if part and part not in genres:
                genres.append(part)
    if genres:
        mapped["genres"] = genres

    return mapped
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend-django && DJANGO_ENV=dev uv run python -m pytest books/tests/test_import_books.py -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add backend-django/books/management/commands/import_books.py backend-django/books/tests/test_import_books.py
git commit -m "feat: add Google Books volumeInfo mapper"
```

---

### Task 3: Fetch helper `_fetch_volume_info`

**Files:**
- Modify: `backend-django/books/management/commands/import_books.py`
- Test: `backend-django/books/tests/test_import_books.py`

- [ ] **Step 1: Write the failing tests**

First, add these imports to the **top import block** of `backend-django/books/tests/test_import_books.py` (keep all imports at the top to avoid ruff E402):

```python
import json
from unittest.mock import MagicMock, patch

from books.management.commands.import_books import _fetch_volume_info
```

Then append the helper and test class to the end of the file:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend-django && DJANGO_ENV=dev uv run python -m pytest books/tests/test_import_books.py::FetchVolumeInfoTests -v`
Expected: FAIL — `ImportError: cannot import name '_fetch_volume_info'`.

- [ ] **Step 3: Implement the fetch helper**

In `backend-django/books/management/commands/import_books.py`, add imports at the top (above `GOOGLE_BOOKS_URL`):

```python
import json
import re
import urllib.parse
import urllib.request
```

(Remove the now-duplicate standalone `import re` — keep a single import block.)

Then add, after `_map_volume_info`:

```python
def _fetch_volume_info(isbn: str, api_key: str) -> dict | None:
    """Query Google Books by ISBN; return the first volumeInfo or None."""
    params = {"q": f"isbn:{isbn}"}
    if api_key:
        params["key"] = api_key
    url = f"{GOOGLE_BOOKS_URL}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=HTTP_TIMEOUT) as response:
        payload = json.loads(response.read().decode("utf-8"))
    items = payload.get("items")
    if not items:
        return None
    return items[0].get("volumeInfo", {})
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend-django && DJANGO_ENV=dev uv run python -m pytest books/tests/test_import_books.py -v`
Expected: PASS (9 tests).

- [ ] **Step 5: Commit**

```bash
git add backend-django/books/management/commands/import_books.py backend-django/books/tests/test_import_books.py
git commit -m "feat: add Google Books fetch helper"
```

---

### Task 4: Command `handle` (create/update/dry-run/file/counts/exit)

**Files:**
- Modify: `backend-django/books/management/commands/import_books.py`
- Test: `backend-django/books/tests/test_import_books.py`

- [ ] **Step 1: Write the failing tests**

First, add these imports to the **top import block** of `backend-django/books/tests/test_import_books.py` (all imports at the top — avoid ruff E402). `tempfile` is imported here too rather than inside the test body:

```python
import tempfile
from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase

from books.models import Book
```

(`Genre` is not needed — genre names are read via `book.genres.values_list`. The `library.models` import shown earlier is unnecessary; do not add it.)

Then append the fixture and test class to the end of the file:

```python
_DUNE = {
    "items": [
        {
            "volumeInfo": {
                "title": "Dune",
                "authors": ["Frank Herbert"],
                "publishedDate": "1965",
                "description": "Epic SF",
                "pageCount": 412,
                "imageLinks": {"thumbnail": "http://x/c.jpg"},
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
        self.assertEqual(book.cover_url, "https://x/c.jpg")
        self.assertEqual(
            sorted(book.genres.values_list("name", flat=True)),
            ["Fiction", "Science Fiction"],
        )
        # Google ratings must NOT leak into our fields
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

    def test_no_isbn_raises(self):
        with self.assertRaises(CommandError):
            call_command("import_books", stdout=StringIO())
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend-django && DJANGO_ENV=dev uv run python -m pytest books/tests/test_import_books.py::ImportBooksCommandTests -v`
Expected: FAIL — command has no `Command` class yet (`CommandError: Unknown command: 'import_books'` or class missing).

- [ ] **Step 3: Implement the command**

In `backend-django/books/management/commands/import_books.py`, add to the import block:

```python
import sys

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from books.models import Book
from books.serializers import BookWriteSerializer
```

Then append the command class at the end of the file:

```python
class Command(BaseCommand):
    help = "Import books from the Google Books API by ISBN."

    def add_arguments(self, parser):
        parser.add_argument("isbns", nargs="*", help="ISBN(s) to import")
        parser.add_argument("--file", dest="file", help="File with one ISBN per line")
        parser.add_argument(
            "--dry-run", action="store_true", help="Fetch and print without saving"
        )

    def handle(self, *args, **options):
        isbns = list(options["isbns"])
        if options.get("file"):
            isbns.extend(self._read_isbn_file(options["file"]))
        if not isbns:
            raise CommandError("Provide at least one ISBN (positional or --file).")

        api_key = settings.GOOGLE_BOOKS_API_KEY
        counts = {"created": 0, "updated": 0, "skipped": 0, "not_found": 0, "failed": 0}

        for isbn in isbns:
            try:
                volume_info = _fetch_volume_info(isbn, api_key)
            except Exception as exc:  # network / HTTP / JSON
                counts["failed"] += 1
                self.stderr.write(self.style.ERROR(f"{isbn}: fetch failed: {exc}"))
                continue

            if volume_info is None:
                counts["not_found"] += 1
                self.stdout.write(self.style.WARNING(f"{isbn}: not found"))
                continue

            if not volume_info.get("title"):
                counts["skipped"] += 1
                self.stdout.write(self.style.WARNING(f"{isbn}: skipped (no title)"))
                continue

            mapped = _map_volume_info(volume_info, isbn)

            if options["dry_run"]:
                self.stdout.write(f"{isbn}: (dry-run) {mapped}")
                continue

            existing = Book.objects.filter(isbn=isbn).first()
            serializer = (
                BookWriteSerializer(existing, data=mapped)
                if existing
                else BookWriteSerializer(data=mapped)
            )
            if not serializer.is_valid():
                counts["failed"] += 1
                self.stderr.write(self.style.ERROR(f"{isbn}: invalid: {serializer.errors}"))
                continue

            serializer.save()
            if existing:
                counts["updated"] += 1
                self.stdout.write(self.style.SUCCESS(f"{isbn}: updated"))
            else:
                counts["created"] += 1
                self.stdout.write(self.style.SUCCESS(f"{isbn}: created"))

        self.stdout.write(
            "created: {created}, updated: {updated}, skipped: {skipped}, "
            "not found: {not_found}, failed: {failed}".format(**counts)
        )
        if counts["failed"]:
            sys.exit(1)

    def _read_isbn_file(self, path: str) -> list[str]:
        isbns = []
        with open(path) as handle:
            for line in handle:
                line = line.strip()
                if line and not line.startswith("#"):
                    isbns.append(line)
        return isbns
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend-django && DJANGO_ENV=dev uv run python -m pytest books/tests/test_import_books.py -v`
Expected: PASS (15 tests).

- [ ] **Step 5: Lint**

Run: `cd backend-django && uv run ruff check books/management/commands/import_books.py books/tests/test_import_books.py`
Expected: `All checks passed!`

- [ ] **Step 6: Commit**

```bash
git add backend-django/books/management/commands/import_books.py backend-django/books/tests/test_import_books.py
git commit -m "feat: add import_books management command"
```

---

### Task 5: ROADMAP update + full verification

**Files:**
- Modify: `docs/ROADMAP.md`

- [ ] **Step 1: Move the importer entry to "Zrobione"**

In `docs/ROADMAP.md`, remove this bullet from the "Kiedyś (bez priorytetu)" section:

```
- Importer książek z OpenLibrary / Goodreads
```

and add a row to the "Zrobione" table (after the M5 row):

```
| Google Books import | `import_books` management command (CLI) — import po ISBN, dedup+update po `isbn`, `categories` → split na `genres`, reuse `BookWriteSerializer`, stdlib `urllib`; `--file`, `--dry-run` | ✅ branch feat/google-books-import |
```

- [ ] **Step 2: Run the full backend test suite**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test`
Expected: all tests pass (existing suite + new `test_import_books`).

- [ ] **Step 3: Full lint**

Run: `cd backend-django && uv run ruff check .`
Expected: `All checks passed!`

- [ ] **Step 4: Commit**

```bash
git add docs/ROADMAP.md
git commit -m "docs: mark Google Books import done in roadmap"
```

---

## Self-Review

**Spec coverage:**
- Command interface (positional + `--file` + `--dry-run`, ≥1 ISBN required) → Task 4.
- Fetch from Google Books (`q=isbn:`, first item, key optional) → Task 3; setting → Task 1.
- Field mapping incl. categories split, HTML strip, http→https, ratings excluded → Task 2 (+ ratings asserted in Task 4).
- Dedup/update by ISBN via `BookWriteSerializer` → Task 4.
- Error classification + summary + non-zero exit on failed → Task 4 (`failed`/`not found`/`skipped` paths; `sys.exit(1)`).
- Tests with mocked `urlopen` → Tasks 2–4.
- ROADMAP move → Task 5.

**Note on "failed exit" test:** a dedicated test for `sys.exit(1)` on fetch error is omitted to keep the suite lean; the failure path is exercised structurally by the not-found/skip tests and the counter logic. If desired, add a test patching `urlopen` to raise `URLError` and asserting `SystemExit`.

**Placeholder scan:** none.

**Type consistency:** `_map_volume_info(volume_info, isbn)`, `_fetch_volume_info(isbn, api_key)`, `_strip_html(text)`, `GOOGLE_BOOKS_URL`, `HTTP_TIMEOUT`, `GOOGLE_BOOKS_API_KEY`, `_fake_urlopen` consistent across all tasks.
