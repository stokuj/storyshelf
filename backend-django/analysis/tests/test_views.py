from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from analysis.models import BookCharacter, CharacterRelationship
from books.models import Book


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def ai_book(db):
    from books.models import Book

    return Book.objects.create(title="AI Book", text="Some text about Alice and Bob.")


class TestAIExtractionPermissions:
    def test_trigger_anonymous_returns_401(self, api_client, ai_book):
        response = api_client.post(f"/api/books/{ai_book.pk}/ai/extract/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_trigger_non_admin_returns_403(self, api_client, regular_user, ai_book):
        api_client.force_authenticate(user=regular_user)
        response = api_client.post(f"/api/books/{ai_book.pk}/ai/extract/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_anonymous_returns_401(self, api_client, ai_book):
        response = api_client.get(f"/api/books/{ai_book.pk}/ai/extraction/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_non_admin_returns_403(self, api_client, regular_user, ai_book):
        api_client.force_authenticate(user=regular_user)
        response = api_client.get(f"/api/books/{ai_book.pk}/ai/extraction/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_hide_anonymous_returns_401(self, db, api_client, ai_book):
        from analysis.models import BookCharacter

        char = BookCharacter.objects.create(book=ai_book, name="Alice", mention_count=3)
        response = api_client.post(f"/api/books/{ai_book.pk}/characters/{char.pk}/hide/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAIExtractionTrigger:
    def test_trigger_returns_202_and_sets_pending(self, db, api_client, admin_user, ai_book):
        api_client.force_authenticate(user=admin_user)
        with patch("analysis.views.analyse_book") as mock_task:
            mock_task.delay = MagicMock()
            response = api_client.post(f"/api/books/{ai_book.pk}/ai/extract/")
        assert response.status_code == status.HTTP_202_ACCEPTED
        mock_task.delay.assert_called_once_with(ai_book.pk)
        ai_book.refresh_from_db()
        assert ai_book.ai_extraction_status == "pending"

    def test_trigger_idempotent_when_pending(self, db, api_client, admin_user, ai_book):
        from books.models import Book

        api_client.force_authenticate(user=admin_user)
        Book.objects.filter(pk=ai_book.pk).update(ai_extraction_status="pending")
        with patch("analysis.views.analyse_book") as mock_task:
            mock_task.delay = MagicMock()
            response = api_client.post(f"/api/books/{ai_book.pk}/ai/extract/")
        assert response.status_code == status.HTTP_200_OK
        mock_task.delay.assert_not_called()
        ai_book.refresh_from_db()
        assert ai_book.ai_extraction_status == "pending"

    def test_trigger_idempotent_when_running(self, db, api_client, admin_user, ai_book):
        from books.models import Book

        api_client.force_authenticate(user=admin_user)
        Book.objects.filter(pk=ai_book.pk).update(ai_extraction_status="running")
        with patch("analysis.views.analyse_book") as mock_task:
            mock_task.delay = MagicMock()
            response = api_client.post(f"/api/books/{ai_book.pk}/ai/extract/")
        assert response.status_code == status.HTTP_200_OK
        mock_task.delay.assert_not_called()

    def test_trigger_404_for_nonexistent_book(self, db, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        response = api_client.post("/api/books/99999/ai/extract/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_returns_extraction_payload_shape(self, db, api_client, admin_user, ai_book):
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f"/api/books/{ai_book.pk}/ai/extraction/")
        assert response.status_code == status.HTTP_200_OK
        expected_keys = (
            "status", "characters", "relations",
            "covered_through", "confidence_summary", "failure_reason",
        )
        for key in expected_keys:
            assert key in response.data

    def test_retrieve_covered_through_stub(self, db, api_client, admin_user, ai_book):
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f"/api/books/{ai_book.pk}/ai/extraction/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["covered_through"]["chapter"] is None

    def test_retrieve_404_for_nonexistent_book(self, db, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/books/99999/ai/extraction/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestBookCharacterHide:
    def test_hide_sets_is_hidden_true(self, db, api_client, admin_user):
        from analysis.models import BookCharacter
        from books.models import Book

        api_client.force_authenticate(user=admin_user)
        book = Book.objects.create(title="Hide Book A")
        char = BookCharacter.objects.create(book=book, name="Visible Character", mention_count=5)

        response = api_client.post(
            f"/api/books/{book.pk}/characters/{char.pk}/hide/",
            {"hidden": True},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        char.refresh_from_db()
        assert char.is_hidden is True

    def test_unhide_sets_is_hidden_false(self, db, api_client, admin_user):
        from analysis.models import BookCharacter
        from books.models import Book

        api_client.force_authenticate(user=admin_user)
        book = Book.objects.create(title="Hide Book B")
        char = BookCharacter.objects.create(
            book=book, name="Hidden Character", mention_count=5, is_hidden=True
        )

        response = api_client.post(
            f"/api/books/{book.pk}/characters/{char.pk}/hide/",
            {"hidden": False},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        char.refresh_from_db()
        assert char.is_hidden is False

    def test_hide_default_true_when_no_body(self, db, api_client, admin_user):
        from analysis.models import BookCharacter
        from books.models import Book

        api_client.force_authenticate(user=admin_user)
        book = Book.objects.create(title="Hide Book C")
        char = BookCharacter.objects.create(book=book, name="Default Hide", mention_count=5)

        response = api_client.post(f"/api/books/{book.pk}/characters/{char.pk}/hide/")
        assert response.status_code == status.HTTP_200_OK
        char.refresh_from_db()
        assert char.is_hidden is True

    def test_hide_404_wrong_book(self, db, api_client, admin_user):
        from analysis.models import BookCharacter
        from books.models import Book

        api_client.force_authenticate(user=admin_user)
        book = Book.objects.create(title="Book X")
        other_book = Book.objects.create(title="Book Y")
        char = BookCharacter.objects.create(book=book, name="Character", mention_count=5)

        response = api_client.post(
            f"/api/books/{other_book.pk}/characters/{char.pk}/hide/",
            {"hidden": True},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ─── BookCharacterMergeView (unittest-style, alongside pytest tests) ─────────

User = get_user_model()


def _make_book():
    return Book.objects.create(title="Test", description="")


def _make_char(book, name, mention_count=5):
    return BookCharacter.objects.create(
        book=book, name=name, mention_count=mention_count
    )


def _make_rel(book, from_char, to_char, rel_type="friend_of"):
    return CharacterRelationship.objects.create(
        book=book,
        from_character=from_char,
        to_character=to_char,
        relation_type=rel_type,
    )


class BookCharacterMergeViewTest(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@test.com",
            handle="admin",
            password="pw123456",
            is_staff=True,
        )
        self.user = User.objects.create_user(
            email="user@test.com", handle="regularuser", password="pw123456"
        )
        self.book = _make_book()
        self.harry = _make_char(self.book, "Harry", mention_count=10)
        self.potter = _make_char(self.book, "Mr. Potter", mention_count=3)

    def _url(self, book_id=None, char_id=None):
        b = book_id or self.book.pk
        c = char_id or self.potter.pk
        return f"/api/books/{b}/characters/{c}/merge/"

    def test_anon_returns_401(self):
        resp = self.client.post(self._url(), {"into": self.harry.pk})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_returns_403(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self._url(), {"into": self.harry.pk})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_merge_sets_canonical_on_source(self):
        self.client.force_authenticate(user=self.admin)
        self.client.post(self._url(), {"into": self.harry.pk})
        self.potter.refresh_from_db()
        self.assertEqual(self.potter.canonical_id, self.harry.pk)

    def test_merge_sets_is_hidden_on_source(self):
        self.client.force_authenticate(user=self.admin)
        self.client.post(self._url(), {"into": self.harry.pk})
        self.potter.refresh_from_db()
        self.assertTrue(self.potter.is_hidden)

    def test_merge_accumulates_mention_count(self):
        self.client.force_authenticate(user=self.admin)
        self.client.post(self._url(), {"into": self.harry.pk})
        self.harry.refresh_from_db()
        self.assertEqual(self.harry.mention_count, 13)  # 10 + 3

    def test_merge_transfers_relations_from_source(self):
        hermione = _make_char(self.book, "Hermione")
        rel = _make_rel(self.book, self.potter, hermione)
        self.client.force_authenticate(user=self.admin)
        self.client.post(self._url(), {"into": self.harry.pk})
        rel.refresh_from_db()
        self.assertEqual(rel.from_character_id, self.harry.pk)

    def test_merge_transfers_relations_to_source(self):
        hermione = _make_char(self.book, "Hermione")
        rel = _make_rel(self.book, hermione, self.potter)
        self.client.force_authenticate(user=self.admin)
        self.client.post(self._url(), {"into": self.harry.pk})
        rel.refresh_from_db()
        self.assertEqual(rel.to_character_id, self.harry.pk)

    def test_merge_removes_duplicate_relations(self):
        hermione = _make_char(self.book, "Hermione")
        _make_rel(self.book, self.harry, hermione)
        _make_rel(self.book, self.potter, hermione)
        self.client.force_authenticate(user=self.admin)
        self.client.post(self._url(), {"into": self.harry.pk})
        rels = CharacterRelationship.objects.filter(
            from_character=self.harry, to_character=hermione
        )
        self.assertEqual(rels.count(), 1)

    def test_merge_returns_200_with_canonical_data(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(self._url(), {"into": self.harry.pk})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["id"], self.harry.pk)

    def test_merge_into_self_returns_400(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(
            self._url(char_id=self.harry.pk), {"into": self.harry.pk}
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_merge_nonexistent_source_returns_404(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(self._url(char_id=9999), {"into": self.harry.pk})
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_merge_target_from_other_book_returns_400(self):
        other_book = _make_book()
        other_char = _make_char(other_book, "Ron")
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(self._url(), {"into": other_char.pk})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_merge_alias_as_source_returns_400(self):
        alias = _make_char(self.book, "Alias")
        alias.canonical = self.harry
        alias.save()
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(
            self._url(char_id=alias.pk), {"into": self.potter.pk}
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_merge_alias_as_target_returns_400(self):
        alias = _make_char(self.book, "Alias")
        alias.canonical = self.harry
        alias.save()
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(self._url(), {"into": alias.pk})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_merge_canonical_with_existing_aliases_transfers_aliases(self):
        alias1 = _make_char(self.book, "HP")
        alias1.canonical = self.potter
        alias1.save()
        self.client.force_authenticate(user=self.admin)
        self.client.post(self._url(), {"into": self.harry.pk})
        alias1.refresh_from_db()
        self.assertEqual(alias1.canonical_id, self.harry.pk)
