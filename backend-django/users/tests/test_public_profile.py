from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from shelf.models import Shelf, ShelfEntry
from users.models import User


class PublicUserShelvesViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            email="owner@test.com", handle="shelfowner", password="pass123",
            profile_public=True,
        )
        self.visitor = User.objects.create_user(
            email="visitor@test.com", handle="visitor", password="pass123"
        )
        self.public_shelf = Shelf.objects.create(
            user=self.owner, name="Public Shelf", is_public=True
        )
        self.private_shelf = Shelf.objects.create(
            user=self.owner, name="Private Shelf", is_public=False
        )

    def test_anon_sees_only_public_shelves(self):
        response = self.client.get(f"/api/users/{self.owner.handle}/shelves/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [s["name"] for s in response.data]
        self.assertIn("Public Shelf", names)
        self.assertNotIn("Private Shelf", names)

    def test_owner_sees_all_shelves(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f"/api/users/{self.owner.handle}/shelves/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [s["name"] for s in response.data]
        self.assertIn("Public Shelf", names)
        self.assertIn("Private Shelf", names)

    def test_private_profile_returns_404_for_visitor(self):
        self.owner.profile_public = False
        self.owner.save()
        self.client.force_authenticate(user=self.visitor)
        response = self.client.get(f"/api/users/{self.owner.handle}/shelves/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_private_profile_owner_can_see_own_shelves(self):
        self.owner.profile_public = False
        self.owner.save()
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f"/api/users/{self.owner.handle}/shelves/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_nonexistent_username_returns_404(self):
        response = self.client.get("/api/users/doesnotexist/shelves/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PublicUserRecentlyReadViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="reader@test.com", handle="reader", password="pass123",
            profile_public=True,
        )
        self.visitor = User.objects.create_user(
            email="vis@test.com", handle="vis", password="pass123"
        )

    def _add_read_entry(self, book, finish_date=None):
        return ShelfEntry.objects.create(
            user=self.user,
            book=book,
            status=ShelfEntry.Status.READ,
            finish_date=finish_date,
        )

    def test_returns_up_to_6_books(self):
        for i in range(8):
            book = Book.objects.create(title=f"Book {i}")
            self._add_read_entry(book)
        response = self.client.get(f"/api/users/{self.user.handle}/recently-read/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data), 6)

    def test_empty_when_no_read_books(self):
        book = Book.objects.create(title="Unread")
        ShelfEntry.objects.create(user=self.user, book=book, status=ShelfEntry.Status.WANT_TO_READ)
        response = self.client.get(f"/api/users/{self.user.handle}/recently-read/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_private_profile_returns_404_for_non_owner(self):
        self.user.profile_public = False
        self.user.save()
        self.client.force_authenticate(user=self.visitor)
        response = self.client.get(f"/api/users/{self.user.handle}/recently-read/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_response_contains_expected_fields(self):
        book = Book.objects.create(title="My Read")
        self._add_read_entry(book)
        response = self.client.get(f"/api/users/{self.user.handle}/recently-read/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        for field in ("id", "title"):
            self.assertIn(field, response.data[0])