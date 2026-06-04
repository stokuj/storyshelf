from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from ratings.models import Rating
from shelf.models import ShelfEntry
from users.models import User


class PublicShelfEntryListViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            email="owner@test.com", handle="reader", password="pass123",
            profile_public=True,
        )
        self.visitor = User.objects.create_user(
            email="visitor@test.com", handle="visitor", password="pass123",
        )
        self.book_a = Book.objects.create(title="Book A", slug="book-a")
        self.book_b = Book.objects.create(title="Book B", slug="book-b")
        # book_b added later -> should sort first (-created_at).
        ShelfEntry.objects.create(user=self.owner, book=self.book_a, status="READ")
        ShelfEntry.objects.create(user=self.owner, book=self.book_b, status="READING")
        Rating.objects.create(user=self.owner, book=self.book_a, rating=5)

    def test_returns_all_owner_entries(self):
        response = self.client.get(f"/api/u/{self.owner.handle}/shelf/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_ordered_newest_first(self):
        response = self.client.get(f"/api/u/{self.owner.handle}/shelf/")
        slugs = [e["book"]["slug"] for e in response.data]
        self.assertEqual(slugs, ["book-b", "book-a"])

    def test_includes_owner_rating(self):
        response = self.client.get(f"/api/u/{self.owner.handle}/shelf/")
        by_slug = {e["book"]["slug"]: e for e in response.data}
        self.assertEqual(by_slug["book-a"]["user_rating"], 5)
        self.assertIsNone(by_slug["book-b"]["user_rating"])

    def test_entry_exposes_status_and_dates(self):
        response = self.client.get(f"/api/u/{self.owner.handle}/shelf/")
        entry = response.data[0]
        self.assertEqual(
            set(entry.keys()),
            {"status", "start_date", "finish_date", "current_page", "user_rating", "book"},
        )

    def test_private_profile_404_for_visitor(self):
        self.owner.profile_public = False
        self.owner.save()
        self.client.force_authenticate(user=self.visitor)
        response = self.client.get(f"/api/u/{self.owner.handle}/shelf/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_private_profile_owner_sees_own(self):
        self.owner.profile_public = False
        self.owner.save()
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f"/api/u/{self.owner.handle}/shelf/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_nonexistent_handle_404(self):
        response = self.client.get("/api/u/ghost/shelf/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
