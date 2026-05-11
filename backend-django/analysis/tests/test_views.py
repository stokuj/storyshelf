from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book, Chapter, BookCharacter, CharacterRelation, StoryCharacter
from config.test_helpers import AuthTestHelper


class InternalEndpointMixin:
    """Override REMOTE_ADDR to bypass InternalEndpointMiddleware."""

    def setUp(self):
        self.client.defaults["REMOTE_ADDR"] = "172.18.0.1"


class AnalyseResultTest(InternalEndpointMixin, AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(title="Analyse Book")
        cls.chapter = Chapter.objects.create(
            book=cls.book, chapter_number=1, title="C1", content="test content"
        )
        cls.url = f"/api/internal/chapters/{cls.chapter.id}/analyse-result/"

    def test_post_valid_returns_200_and_updates_chapter(self):
        resp = self.client.post(
            self.url,
            {
                "char_count": 100,
                "char_count_clean": 90,
                "word_count": 20,
                "token_count": 25,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.chapter.refresh_from_db()
        self.assertEqual(self.chapter.char_count, 100)
        self.assertEqual(self.chapter.char_count_clean, 90)
        self.assertEqual(self.chapter.word_count, 20)
        self.assertEqual(self.chapter.token_count, 25)
        self.assertTrue(self.chapter.analysis_completed)

    def test_post_second_time_returns_200_idempotent(self):
        self.client.post(self.url, {"char_count": 50}, format="json")
        resp = self.client.post(self.url, {"char_count": 999}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.chapter.refresh_from_db()
        self.assertEqual(self.chapter.char_count, 50)

    def test_post_nonexistent_chapter_returns_500(self):
        resp = self.client.post(
            "/api/internal/chapters/99999/analyse-result/",
            {"char_count": 1},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_post_zero_values_are_preserved(self):
        resp = self.client.post(
            self.url,
            {
                "char_count": 0,
                "char_count_clean": 0,
                "word_count": 0,
                "token_count": 0,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.chapter.refresh_from_db()
        self.assertEqual(self.chapter.char_count, 0)
        self.assertEqual(self.chapter.char_count_clean, 0)
        self.assertEqual(self.chapter.word_count, 0)
        self.assertEqual(self.chapter.token_count, 0)

    def test_post_blocked_without_docker_ip(self):
        old = self.client.defaults.pop("REMOTE_ADDR", None)
        resp = self.client.post(self.url, {"char_count": 1}, format="json")
        if old is not None:
            self.client.defaults["REMOTE_ADDR"] = old
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class NerResultTest(InternalEndpointMixin, AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(title="NER Book", chapters_count=2)
        cls.chapter1 = Chapter.objects.create(
            book=cls.book,
            chapter_number=1,
            title="C1",
            content="Alice and Bob",
            analysis_completed=True,
        )
        cls.chapter2 = Chapter.objects.create(
            book=cls.book,
            chapter_number=2,
            title="C2",
            content="More text",
            analysis_completed=True,
        )
        cls.url = f"/api/internal/chapters/{cls.chapter1.id}/ner-result/"

    @patch("analysis.callbacks.find_pairs.delay")
    def test_post_valid_creates_characters(self, mock_find_pairs):
        resp = self.client.post(
            self.url, {"result": {"characters": {"Alice": 5, "Bob": 3}}}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.chapter1.refresh_from_db()
        self.assertIsNotNone(self.chapter1.ner_result)
        self.assertEqual(self.chapter1.ner_result["characters"]["Alice"], 5)
        self.assertTrue(StoryCharacter.objects.filter(name="Alice").exists())
        self.assertTrue(StoryCharacter.objects.filter(name="Bob").exists())
        bc = BookCharacter.objects.get(book=self.book, character__name="Alice")
        self.assertEqual(bc.mention_count, 5)

    @patch("analysis.callbacks.find_pairs.delay")
    def test_post_second_time_returns_200_idempotent(self, mock_find_pairs):
        self.client.post(
            self.url, {"result": {"characters": {"Alice": 5}}}, format="json"
        )
        resp = self.client.post(
            self.url, {"result": {"characters": {"Charlie": 99}}}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(StoryCharacter.objects.filter(name="Charlie").exists())

    @patch("analysis.callbacks.find_pairs.delay")
    def test_post_triggers_find_pairs_when_all_chapters_done(self, mock_find_pairs):
        self.chapter2.ner_result = {"characters": {}}
        self.chapter2.save()
        self.book.refresh_from_db()
        self.book.ner_completed_count = 1
        self.book.chapters_count = 2
        self.book.save()

        resp = self.client.post(
            self.url, {"result": {"characters": {"Alice": 1}}}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        mock_find_pairs.assert_called_once_with(self.book.id)

    def test_post_blocked_without_docker_ip(self):
        old = self.client.defaults.pop("REMOTE_ADDR", None)
        resp = self.client.post(self.url, {}, format="json")
        if old is not None:
            self.client.defaults["REMOTE_ADDR"] = old
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class FindPairsResultTest(InternalEndpointMixin, AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(title="Pairs Book")
        cls.sc1 = StoryCharacter.objects.create(name="Alice")
        cls.sc2 = StoryCharacter.objects.create(name="Bob")
        cls.url = f"/api/internal/books/{cls.book.id}/find-pairs-result/"

    @patch("analysis.callbacks.relations_for_book.delay")
    def test_post_valid_creates_relations(self, mock_relations):
        resp = self.client.post(
            self.url,
            {
                "pairs": [
                    {"pair": ["Alice", "Bob"]},
                    {"pair": ["Alice", "Charlie"]},
                ]
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(
            CharacterRelation.objects.filter(
                book=self.book, source__name="Alice", target__name="Bob"
            ).exists()
        )
        self.assertTrue(
            CharacterRelation.objects.filter(
                book=self.book, source__name="Alice", target__name="Charlie"
            ).exists()
        )
        mock_relations.assert_called_once_with(self.book.id)

    @patch("analysis.callbacks.relations_for_book.delay")
    def test_post_second_time_returns_200_idempotent(self, mock_relations):
        resp = self.client.post(
            self.url, {"pairs": [{"pair": ["Alice", "Bob"]}]}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(CharacterRelation.objects.filter(book=self.book).count(), 1)

        mock_relations.reset_mock()
        resp = self.client.post(
            self.url, {"pairs": [{"pair": ["Alice", "Bob"]}]}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(CharacterRelation.objects.filter(book=self.book).count(), 1)
        mock_relations.assert_not_called()


class RelationsResultTest(InternalEndpointMixin, AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.book = Book.objects.create(title="Relations Book")
        cls.sc1 = StoryCharacter.objects.create(name="Alice")
        cls.sc2 = StoryCharacter.objects.create(name="Bob")
        cls.cr = CharacterRelation.objects.create(
            book=cls.book,
            source=cls.sc1,
            target=cls.sc2,
        )
        cls.url = f"/api/internal/books/{cls.book.id}/relations-result/"

    def test_post_valid_updates_relation(self):
        resp = self.client.post(
            self.url,
            {
                "all_relations": [
                    {
                        "relations": {
                            "relations": [
                                {
                                    "source": "Alice",
                                    "target": "Bob",
                                    "relation": "friends",
                                    "evidence": "text",
                                    "confidence": 0.9,
                                }
                            ]
                        }
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.cr.refresh_from_db()
        self.assertEqual(self.cr.relation, "friends")
        self.assertEqual(self.cr.evidence, "text")
        self.assertEqual(self.cr.confidence, 0.9)

    def test_post_empty_relations_returns_200(self):
        resp = self.client.post(self.url, {"all_relations": []}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_post_blocked_without_docker_ip(self):
        old = self.client.defaults.pop("REMOTE_ADDR", None)
        resp = self.client.post(self.url, {}, format="json")
        if old is not None:
            self.client.defaults["REMOTE_ADDR"] = old
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
