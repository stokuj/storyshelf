from unittest.mock import patch

from django.db import IntegrityError
from django.test import TestCase

from books.models import Book, _generate_unique_slug


class BookSlugGenerationTest(TestCase):
    def test_slug_generated_on_save(self):
        book = Book.objects.create(title="The Great Gatsby")
        self.assertEqual(book.slug, "the-great-gatsby")

    def test_slug_collision_adds_suffix(self):
        Book.objects.create(title="Dune")
        book2 = Book.objects.create(title="Dune")
        self.assertNotEqual(book2.slug, "dune")
        self.assertTrue(book2.slug.startswith("dune-"))

    def test_slug_not_changed_on_title_update(self):
        book = Book.objects.create(title="Original Title")
        original_slug = book.slug
        book.title = "Changed Title"
        book.save()
        book.refresh_from_db()
        self.assertEqual(book.slug, original_slug)

    def test_isbn_collision_does_not_trigger_slug_retry(self):
        # A duplicate isbn is a real error, not a slug race — it must surface
        # immediately without re-running the slug generator in the retry loop.
        Book.objects.create(title="First", isbn="9780000000001")
        with patch(
            "books.models._generate_unique_slug", wraps=_generate_unique_slug
        ) as gen:
            with self.assertRaises(IntegrityError):
                Book.objects.create(title="Second", isbn="9780000000001")
        self.assertEqual(gen.call_count, 1)
