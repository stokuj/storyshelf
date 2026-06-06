from unittest.mock import patch

from django.conf import settings
from django.test import TestCase

from books.models import Book
from characters.models import Character, CharacterAnalysis
from characters.tasks import generate_characters_task


class GenerateTaskTests(TestCase):
    def setUp(self):
        self.book = Book.objects.create(title="Dune")
        self.analysis = CharacterAnalysis.objects.create(book=self.book)

    def test_success_stores_characters_and_marks_done(self):
        fake = {
            "characters": [{"name": "Paul", "role": "Protagonist", "description": "Heir."}],
            "relations": [],
        }
        with patch("characters.tasks.generate_characters", return_value=fake):
            generate_characters_task(self.book.id)

        self.analysis.refresh_from_db()
        self.assertEqual(self.analysis.status, CharacterAnalysis.Status.DONE)
        self.assertEqual(self.analysis.model, settings.OPENROUTER_MODEL)
        self.assertEqual(Character.objects.filter(book=self.book).count(), 1)

    def test_failure_marks_failed_with_message(self):
        from characters.ai import CharacterGenerationError

        with patch(
            "characters.tasks.generate_characters",
            side_effect=CharacterGenerationError("boom"),
        ):
            generate_characters_task(self.book.id)

        self.analysis.refresh_from_db()
        self.assertEqual(self.analysis.status, CharacterAnalysis.Status.FAILED)
        self.assertIn("boom", self.analysis.error_message)
        self.assertEqual(Character.objects.filter(book=self.book).count(), 0)
