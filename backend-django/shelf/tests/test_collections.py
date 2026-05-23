from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from shelf.models import Shelf, ShelfMembership
from users.models import User


class MyShelvesViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="shelf@test.com", handle="shelfuser", password="pass123"
        )
        self.other = User.objects.create_user(
            email="other@test.com", handle="otheruser", password="pass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_list_own_shelves_only(self):
        Shelf.objects.create(user=self.user, name="Mine")
        Shelf.objects.create(user=self.other, name="Theirs")
        response = self.client.get("/api/shelf/me/collections/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [s["name"] for s in response.data]
        self.assertIn("Mine", names)
        self.assertNotIn("Theirs", names)

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        response = self.client.get("/api/shelf/me/collections/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_shelf_returns_201_with_slug(self):
        response = self.client.post(
            "/api/shelf/me/collections/",
            {"name": "Ulubione kryminały"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["slug"], "ulubione-kryminay")

    def test_create_duplicate_name_generates_slug_suffix(self):
        self.client.post("/api/shelf/me/collections/", {"name": "Ulubione"}, format="json")
        response = self.client.post(
            "/api/shelf/me/collections/", {"name": "Ulubione"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["slug"], "ulubione-2")

    def test_create_without_name_returns_400(self):
        response = self.client.post(
            "/api/shelf/me/collections/", {"description": "No name"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_default_is_public_false(self):
        response = self.client.post(
            "/api/shelf/me/collections/", {"name": "Secret shelf"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data["is_public"])


class MyShelfDetailViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="detail@test.com", handle="detailuser", password="pass123"
        )
        self.client.force_authenticate(user=self.user)
        self.shelf = Shelf.objects.create(user=self.user, name="My Shelf")
        self.book = Book.objects.create(title="Test Book")

    def test_get_detail_contains_books(self):
        ShelfMembership.objects.create(shelf=self.shelf, book=self.book)
        response = self.client.get(f"/api/shelf/me/collections/{self.shelf.slug}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("books", response.data)
        self.assertEqual(len(response.data["books"]), 1)

    def test_patch_updates_name_not_slug(self):
        original_slug = self.shelf.slug
        response = self.client.patch(
            f"/api/shelf/me/collections/{self.shelf.slug}/",
            {"name": "Renamed Shelf"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.shelf.refresh_from_db()
        self.assertEqual(self.shelf.slug, original_slug)
        self.assertEqual(self.shelf.name, "Renamed Shelf")

    def test_patch_is_public(self):
        response = self.client.patch(
            f"/api/shelf/me/collections/{self.shelf.slug}/",
            {"is_public": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.shelf.refresh_from_db()
        self.assertTrue(self.shelf.is_public)

    def test_delete_shelf_and_memberships(self):
        ShelfMembership.objects.create(shelf=self.shelf, book=self.book)
        response = self.client.delete(f"/api/shelf/me/collections/{self.shelf.slug}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Shelf.objects.filter(pk=self.shelf.pk).exists())
        self.assertFalse(ShelfMembership.objects.filter(shelf=self.shelf).exists())

    def test_get_nonexistent_returns_404(self):
        response = self.client.get("/api/shelf/me/collections/nonexistent-slug/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class MyShelfBookViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="book@test.com", handle="bookuser", password="pass123"
        )
        self.other = User.objects.create_user(
            email="other2@test.com", handle="otheruser2", password="pass123"
        )
        self.client.force_authenticate(user=self.user)
        self.shelf = Shelf.objects.create(user=self.user, name="Reading List")
        self.book = Book.objects.create(title="Great Book")

    def test_add_book_returns_201(self):
        response = self.client.post(
            f"/api/shelf/me/collections/{self.shelf.slug}/books/{self.book.pk}/"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ShelfMembership.objects.filter(shelf=self.shelf, book=self.book).exists())

    def test_add_book_idempotent(self):
        self.client.post(f"/api/shelf/me/collections/{self.shelf.slug}/books/{self.book.pk}/")
        response = self.client.post(
            f"/api/shelf/me/collections/{self.shelf.slug}/books/{self.book.pk}/"
        )
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertEqual(
            ShelfMembership.objects.filter(shelf=self.shelf, book=self.book).count(), 1
        )

    def test_add_book_to_other_users_shelf_returns_404(self):
        other_shelf = Shelf.objects.create(user=self.other, name="Other Shelf")
        response = self.client.post(
            f"/api/shelf/me/collections/{other_shelf.slug}/books/{self.book.pk}/"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_nonexistent_book_returns_404(self):
        response = self.client.post(
            f"/api/shelf/me/collections/{self.shelf.slug}/books/99999/"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_remove_book_returns_204(self):
        ShelfMembership.objects.create(shelf=self.shelf, book=self.book)
        response = self.client.delete(
            f"/api/shelf/me/collections/{self.shelf.slug}/books/{self.book.pk}/"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ShelfMembership.objects.filter(shelf=self.shelf, book=self.book).exists())

    def test_remove_book_not_in_shelf_returns_404(self):
        response = self.client.delete(
            f"/api/shelf/me/collections/{self.shelf.slug}/books/{self.book.pk}/"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
