from django.test import TestCase

from books.models import Book
from characters.models import Character, CharacterRelation
from characters.services import store_characters


class StoreCharactersTests(TestCase):
    def test_duplicate_relation_deduped_and_missing_endpoint_skipped(self):
        book = Book.objects.create(title="T", slug="t")
        data = {
            "characters": [{"name": "Alice"}, {"name": "Bob"}],
            "relations": [
                {"from": "Alice", "to": "Bob", "type": "friend"},
                {"from": "Alice", "to": "Bob", "type": "friend"},
                {"from": "Alice", "to": "Ghost", "type": "friend"},
            ],
        }
        store_characters(book, data)
        self.assertEqual(Character.objects.filter(book=book).count(), 2)
        self.assertEqual(CharacterRelation.objects.filter(book=book).count(), 1)
