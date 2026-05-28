from django.core.management import call_command
from django.test import TestCase

from books.models import Book


class SeedCommandTests(TestCase):
    """Tests for `manage.py seed_books` command."""

    def test_seed_from_fixtures_creates_books(self):
        call_command("seed_books", verbosity=0)
        self.assertGreater(Book.objects.count(), 0)

    def test_seed_slugs_are_unique(self):
        call_command("seed_books", verbosity=0)
        slugs = list(Book.objects.values_list("slug", flat=True))
        self.assertEqual(len(slugs), len(set(slugs)))
