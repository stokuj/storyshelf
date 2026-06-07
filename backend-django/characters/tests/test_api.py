from unittest.mock import patch

from rest_framework.test import APITestCase

from books.models import Book
from characters.models import Character, CharacterAnalysis
from users.models import User


class CharacterApiTests(APITestCase):
    def setUp(self):
        self.book = Book.objects.create(title="Dune")
        self.user = User.objects.create_user(
            email="a@example.com", handle="ann", password="passw0rd123"
        )

    def _generate_url(self):
        return f"/api/books/{self.book.slug}/characters/generate/"

    def test_generate_requires_auth(self):
        res = self.client.post(self._generate_url())
        self.assertEqual(res.status_code, 401)

    def test_generate_enqueues_and_returns_pending(self):
        self.client.force_authenticate(self.user)
        with patch("characters.views.generate_characters_task.delay") as delay:
            res = self.client.post(self._generate_url())
        self.assertEqual(res.status_code, 202)
        self.assertEqual(res.data["status"], "pending")
        delay.assert_called_once_with(self.book.id)

    def test_generate_is_idempotent_while_running(self):
        self.client.force_authenticate(self.user)
        CharacterAnalysis.objects.create(
            book=self.book, status=CharacterAnalysis.Status.RUNNING
        )
        with patch("characters.views.generate_characters_task.delay") as delay:
            res = self.client.post(self._generate_url())
        self.assertEqual(res.status_code, 202)
        self.assertEqual(res.data["status"], "running")
        delay.assert_not_called()

    def test_list_is_public(self):
        CharacterAnalysis.objects.create(book=self.book, status=CharacterAnalysis.Status.DONE)
        Character.objects.create(book=self.book, name="Paul", slug="paul", role="Lead", order=0)
        res = self.client.get(f"/api/books/{self.book.slug}/characters/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["status"], "done")
        self.assertEqual(res.data["characters"][0]["slug"], "paul")

    def test_detail_returns_relations(self):
        paul = Character.objects.create(book=self.book, name="Paul", slug="paul", order=0)
        jess = Character.objects.create(book=self.book, name="Jessica", slug="jessica", order=1)
        from characters.models import CharacterRelation
        from characters.relations import RelationType

        CharacterRelation.objects.create(
            book=self.book,
            from_character=paul,
            to_character=jess,
            relation_type=RelationType.PARENT,
        )
        res = self.client.get(f"/api/books/{self.book.slug}/characters/paul/")
        self.assertEqual(res.status_code, 200)
        rel = res.data["relations"][0]
        self.assertEqual(rel["to_slug"], "jessica")
        self.assertEqual(rel["type"], "parent")
        self.assertEqual(rel["type_display"], "Parent")
        self.assertEqual(rel["group"], "family")

    def test_character_detail_resolves_unicode_slug(self):
        Character.objects.create(book=self.book, name="Цири", slug="цири", order=0)
        res = self.client.get(f"/api/books/{self.book.slug}/characters/цири/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["slug"], "цири")
