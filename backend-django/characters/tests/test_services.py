from django.test import TestCase

from books.models import Book
from characters.models import Character, CharacterRelation
from characters.services import store_characters


class StoreCharactersTests(TestCase):
    def setUp(self):
        self.book = Book.objects.create(title="Dune")

    def test_creates_characters_and_relations(self):
        data = {
            "characters": [
                {"name": "Paul Atreides", "role": "Protagonist", "description": "Heir."},
                {"name": "Lady Jessica", "role": "Mother", "description": "Bene Gesserit."},
            ],
            "relations": [
                {"from": "Paul Atreides", "to": "Lady Jessica", "label": "son"},
            ],
        }
        store_characters(self.book, data)

        self.assertEqual(Character.objects.filter(book=self.book).count(), 2)
        rel = CharacterRelation.objects.get(book=self.book)
        self.assertEqual(rel.from_character.name, "Paul Atreides")
        self.assertEqual(rel.to_character.name, "Lady Jessica")
        self.assertEqual(rel.label, "son")
        self.assertEqual(Character.objects.get(name="Paul Atreides").order, 0)

    def test_caps_at_12_characters(self):
        data = {
            "characters": [
                {"name": f"Char {i}", "role": "x", "description": "y"} for i in range(20)
            ],
            "relations": [],
        }
        store_characters(self.book, data)
        self.assertEqual(Character.objects.filter(book=self.book).count(), 12)

    def test_skips_relations_with_unknown_endpoints(self):
        data = {
            "characters": [{"name": "Paul", "role": "x", "description": "y"}],
            "relations": [{"from": "Paul", "to": "Ghost", "label": "knows"}],
        }
        store_characters(self.book, data)
        self.assertEqual(CharacterRelation.objects.filter(book=self.book).count(), 0)

    def test_replaces_previous_characters(self):
        store_characters(
            self.book,
            {"characters": [{"name": "Old", "role": "", "description": ""}], "relations": []},
        )
        store_characters(
            self.book,
            {"characters": [{"name": "New", "role": "", "description": ""}], "relations": []},
        )
        names = list(Character.objects.filter(book=self.book).values_list("name", flat=True))
        self.assertEqual(names, ["New"])
