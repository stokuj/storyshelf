import json
import re
import sys
import urllib.parse
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from books.models import Book
from books.serializers import BookWriteSerializer

GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"
HTTP_TIMEOUT = 10


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def _map_volume_info(volume_info: dict, isbn: str) -> dict:
    """Map a Google Books volumeInfo dict to BookWriteSerializer input.

    Absent fields are omitted, never set to a falsy value. Google's
    averageRating/ratingsCount are never mapped. `tags` is never set (Google has
    no tag concept). M2M fields (authors/genres/tags) absent here are preserved
    on update — the command seeds them from the existing book (see Command.handle)
    so they are overwritten only when Google actually supplied them.
    """
    mapped: dict = {"isbn": isbn}

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
            if existing:
                # The serializer's default=list turns an absent M2M field into []
                # on update, which _set_m2m treats as "clear". So a field Google
                # didn't return would wipe admin-curated data. Seed each M2M from
                # the existing book so it is overwritten only when Google supplied
                # it, and otherwise preserved.
                for field, manager in (
                    ("tags", existing.tags),
                    ("authors", existing.authors),
                    ("genres", existing.genres),
                ):
                    mapped.setdefault(field, list(manager.values_list("name", flat=True)))
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
