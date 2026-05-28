import os
import sys

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from books.models import Book


class Command(BaseCommand):
    help = "Seed books from the committed fixture."

    def handle(self, *args, **options):
        if Book.objects.exists():
            self.stdout.write(self.style.WARNING("Books already exist; skipping seed."))
            return
        self._load_fixture()
        count = Book.objects.count()
        self.stdout.write(self.style.SUCCESS(f"Seeded {count} books from fixture."))

    def _load_fixture(self):
        fixture_path = os.path.join(
            settings.BASE_DIR, "books", "fixtures", "seed_books.json"
        )
        if not os.path.exists(fixture_path):
            self.stdout.write(self.style.ERROR(f"Fixture not found: {fixture_path}"))
            sys.exit(1)
        call_command("loaddata", "seed_books", verbosity=0)
