from unittest.mock import MagicMock, patch

import pytest
from rest_framework import status
from rest_framework.test import APIClient


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
