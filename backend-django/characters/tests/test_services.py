from django.test import TestCase

from books.models import Book
from characters.ai import MAX_CHARACTERS
from characters.models import Character, CharacterRelation
from characters.relations import RelationType
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
                {"from": "Paul Atreides", "to": "Lady Jessica", "type": "parent"},
            ],
        }
        store_characters(self.book, data)

        self.assertEqual(Character.objects.filter(book=self.book).count(), 2)
        rel = CharacterRelation.objects.get(book=self.book)
        self.assertEqual(rel.from_character.name, "Paul Atreides")
        self.assertEqual(rel.to_character.name, "Lady Jessica")
        self.assertEqual(rel.relation_type, RelationType.PARENT)
        self.assertEqual(Character.objects.get(name="Paul Atreides").order, 0)

    def test_caps_at_12_characters(self):
        data = {
            "characters": [
                {"name": f"Char {i}", "role": "x", "description": "y"} for i in range(20)
            ],
            "relations": [],
        }
        store_characters(self.book, data)
        self.assertEqual(Character.objects.filter(book=self.book).count(), MAX_CHARACTERS)

    def test_skips_relations_with_unknown_endpoints(self):
        data = {
            "characters": [{"name": "Paul", "role": "x", "description": "y"}],
            "relations": [{"from": "Paul", "to": "Ghost", "type": "friend"}],
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

    def test_skips_non_dict_character_items(self):
        data = {
            "characters": [None, "Paul", {"name": "Real", "role": "x", "description": "y"}],
            "relations": [],
        }
        store_characters(self.book, data)
        self.assertEqual(Character.objects.filter(book=self.book).count(), 1)
        self.assertEqual(Character.objects.get(book=self.book).name, "Real")

    def test_skips_self_relation(self):
        data = {
            "characters": [
                {"name": "Paul", "role": "x", "description": "y"},
                {"name": "Jess", "role": "x", "description": "y"},
            ],
            "relations": [{"from": "Paul", "to": "Paul", "type": "sibling"}],
        }
        store_characters(self.book, data)
        self.assertEqual(CharacterRelation.objects.filter(book=self.book).count(), 0)

    def test_dedupes_same_pair_and_type(self):
        data = {
            "characters": [
                {"name": "Paul", "role": "x", "description": "y"},
                {"name": "Jess", "role": "x", "description": "y"},
            ],
            "relations": [
                {"from": "Paul", "to": "Jess", "type": "friend"},
                {"from": "Paul", "to": "Jess", "type": "friend"},
            ],
        }
        store_characters(self.book, data)
        self.assertEqual(CharacterRelation.objects.filter(book=self.book).count(), 1)

    def test_same_pair_different_types_kept(self):
        data = {
            "characters": [
                {"name": "Paul", "role": "x", "description": "y"},
                {"name": "Chani", "role": "x", "description": "y"},
            ],
            "relations": [
                {"from": "Paul", "to": "Chani", "type": "lover"},
                {"from": "Paul", "to": "Chani", "type": "ally"},
            ],
        }
        store_characters(self.book, data)
        types = set(
            CharacterRelation.objects.filter(book=self.book).values_list(
                "relation_type", flat=True
            )
        )
        self.assertEqual(types, {RelationType.LOVER, RelationType.ALLY})

    def test_unknown_type_falls_back_to_other(self):
        data = {
            "characters": [
                {"name": "Paul", "role": "x", "description": "y"},
                {"name": "Jess", "role": "x", "description": "y"},
            ],
            "relations": [{"from": "Paul", "to": "Jess", "type": "frenemy"}],
        }
        store_characters(self.book, data)
        rel = CharacterRelation.objects.get(book=self.book)
        self.assertEqual(rel.relation_type, RelationType.OTHER)

    def test_type_matching_is_case_insensitive(self):
        data = {
            "characters": [
                {"name": "Paul", "role": "x", "description": "y"},
                {"name": "Leto", "role": "x", "description": "y"},
            ],
            "relations": [{"from": "Paul", "to": "Leto", "type": "PARENT"}],
        }
        store_characters(self.book, data)
        rel = CharacterRelation.objects.get(book=self.book)
        self.assertEqual(rel.relation_type, RelationType.PARENT)
