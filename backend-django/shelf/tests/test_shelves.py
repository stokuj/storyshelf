from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APITestCase

from books.models import Book
from shelf.models import Shelf, ShelfMembership

User = get_user_model()


class ShelfModelTests(TestCase):
    def setUp(self):
        self.u1 = User.objects.create_user(email="a@x.com", handle="alice", password="pw")
        self.u2 = User.objects.create_user(email="b@x.com", handle="bob", password="pw")
        self.book = Book.objects.create(title="Dune")

    def test_slug_generated_from_name(self):
        shelf = Shelf.objects.create(owner=self.u1, name="My Fantasy")
        self.assertEqual(shelf.slug, "my-fantasy")

    def test_slug_unique_per_owner_suffixes(self):
        # Two names that differ as strings (so the owner+name constraint is satisfied)
        # but slugify to the same base — slug dedup adds the "-N" suffix.
        s1 = Shelf.objects.create(owner=self.u1, name="Sci Fi")
        s2 = Shelf.objects.create(owner=self.u1, name="Sci-Fi!")
        self.assertNotEqual(s1.slug, s2.slug)

    def test_same_slug_allowed_across_owners(self):
        s1 = Shelf.objects.create(owner=self.u1, name="Fantasy")
        s2 = Shelf.objects.create(owner=self.u2, name="Fantasy")
        self.assertEqual(s1.slug, s2.slug)

    def test_duplicate_name_per_owner_rejected(self):
        Shelf.objects.create(owner=self.u1, name="Fantasy")
        with self.assertRaises(IntegrityError):
            Shelf.objects.create(owner=self.u1, name="Fantasy")

    def test_slug_immutable_on_rename(self):
        shelf = Shelf.objects.create(owner=self.u1, name="Original")
        original_slug = shelf.slug
        shelf.name = "Renamed Entirely"
        shelf.save()
        shelf.refresh_from_db()
        self.assertEqual(shelf.slug, original_slug)

    def test_membership_unique_per_shelf_book(self):
        shelf = Shelf.objects.create(owner=self.u1, name="Fantasy")
        ShelfMembership.objects.create(shelf=shelf, book=self.book)
        with self.assertRaises(IntegrityError):
            ShelfMembership.objects.create(shelf=shelf, book=self.book)


class ShelfCrudTests(APITestCase):
    def setUp(self):
        self.alice = User.objects.create_user(email="a@x.com", handle="alice", password="pw")
        self.bob = User.objects.create_user(email="b@x.com", handle="bob", password="pw")
        self.book = Book.objects.create(title="Dune")

    def test_create_and_list_own_shelves(self):
        self.client.force_authenticate(self.alice)
        res = self.client.post("/api/shelves/", {"name": "Fantasy", "is_public": True})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["slug"], "fantasy")

        res = self.client.get("/api/shelves/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["book_count"], 0)

    def test_list_excludes_other_users_shelves(self):
        Shelf.objects.create(owner=self.bob, name="Bob Shelf")
        self.client.force_authenticate(self.alice)
        res = self.client.get("/api/shelves/")
        self.assertEqual(len(res.data), 0)

    def test_patch_updates_own_shelf(self):
        shelf = Shelf.objects.create(owner=self.alice, name="Fantasy")
        self.client.force_authenticate(self.alice)
        res = self.client.patch(f"/api/shelves/{shelf.slug}/", {"is_public": True})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data["is_public"])
        shelf.refresh_from_db()
        self.assertEqual(shelf.slug, "fantasy")  # slug stable after rename/update

    def test_cannot_patch_other_users_shelf(self):
        shelf = Shelf.objects.create(owner=self.bob, name="Bob Shelf")
        self.client.force_authenticate(self.alice)
        res = self.client.patch(f"/api/shelves/{shelf.slug}/", {"is_public": True})
        self.assertEqual(res.status_code, 404)

    def test_delete_own_shelf(self):
        shelf = Shelf.objects.create(owner=self.alice, name="Fantasy")
        self.client.force_authenticate(self.alice)
        res = self.client.delete(f"/api/shelves/{shelf.slug}/")
        self.assertEqual(res.status_code, 204)
        self.assertFalse(Shelf.objects.filter(pk=shelf.pk).exists())

    def test_duplicate_name_returns_400(self):
        Shelf.objects.create(owner=self.alice, name="Fantasy")
        self.client.force_authenticate(self.alice)
        res = self.client.post("/api/shelves/", {"name": "Fantasy"})
        self.assertEqual(res.status_code, 400)

    def test_create_requires_auth(self):
        res = self.client.post("/api/shelves/", {"name": "Fantasy"})
        self.assertEqual(res.status_code, 401)


class ShelfMembershipTests(APITestCase):
    def setUp(self):
        self.alice = User.objects.create_user(email="a@x.com", handle="alice", password="pw")
        self.bob = User.objects.create_user(email="b@x.com", handle="bob", password="pw")
        self.book = Book.objects.create(title="Dune")
        self.shelf = Shelf.objects.create(owner=self.alice, name="Fantasy")

    def test_add_book(self):
        self.client.force_authenticate(self.alice)
        res = self.client.post(
            f"/api/shelves/{self.shelf.slug}/books/", {"book_slug": self.book.slug}
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(self.shelf.memberships.count(), 1)

    def test_add_book_idempotent(self):
        self.client.force_authenticate(self.alice)
        self.client.post(f"/api/shelves/{self.shelf.slug}/books/", {"book_slug": self.book.slug})
        res = self.client.post(
            f"/api/shelves/{self.shelf.slug}/books/", {"book_slug": self.book.slug}
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.shelf.memberships.count(), 1)

    def test_add_unknown_book_404(self):
        self.client.force_authenticate(self.alice)
        res = self.client.post(f"/api/shelves/{self.shelf.slug}/books/", {"book_slug": "nope"})
        self.assertEqual(res.status_code, 404)

    def test_remove_book(self):
        ShelfMembership.objects.create(shelf=self.shelf, book=self.book)
        self.client.force_authenticate(self.alice)
        res = self.client.delete(f"/api/shelves/{self.shelf.slug}/books/{self.book.slug}/")
        self.assertEqual(res.status_code, 204)
        self.assertEqual(self.shelf.memberships.count(), 0)

    def test_remove_book_idempotent(self):
        self.client.force_authenticate(self.alice)
        res = self.client.delete(f"/api/shelves/{self.shelf.slug}/books/{self.book.slug}/")
        self.assertEqual(res.status_code, 204)

    def test_cannot_add_to_other_users_shelf(self):
        self.client.force_authenticate(self.bob)
        res = self.client.post(
            f"/api/shelves/{self.shelf.slug}/books/", {"book_slug": self.book.slug}
        )
        self.assertEqual(res.status_code, 404)

    def test_retrieve_shelf_lists_books(self):
        ShelfMembership.objects.create(shelf=self.shelf, book=self.book)
        self.client.force_authenticate(self.alice)
        res = self.client.get(f"/api/shelves/{self.shelf.slug}/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data["books"]), 1)
        self.assertEqual(res.data["books"][0]["slug"], self.book.slug)


class PublicShelfTests(APITestCase):
    def setUp(self):
        self.alice = User.objects.create_user(
            email="a@x.com", handle="alice", password="pw", profile_public=True
        )
        self.book = Book.objects.create(title="Dune")
        self.public = Shelf.objects.create(owner=self.alice, name="Public", is_public=True)
        self.private = Shelf.objects.create(owner=self.alice, name="Private", is_public=False)
        ShelfMembership.objects.create(shelf=self.public, book=self.book)

    def test_public_list_returns_only_public_shelves(self):
        res = self.client.get("/api/u/alice/shelves/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["slug"], "public")

    def test_public_detail_lists_books(self):
        res = self.client.get("/api/u/alice/shelves/public/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data["books"]), 1)

    def test_private_shelf_detail_404(self):
        res = self.client.get("/api/u/alice/shelves/private/")
        self.assertEqual(res.status_code, 404)

    def test_private_profile_hides_all_shelves(self):
        self.alice.profile_public = False
        self.alice.save(update_fields=["profile_public"])
        self.assertEqual(self.client.get("/api/u/alice/shelves/").status_code, 404)
        self.assertEqual(self.client.get("/api/u/alice/shelves/public/").status_code, 404)

    def test_unknown_handle_404(self):
        self.assertEqual(self.client.get("/api/u/ghost/shelves/").status_code, 404)
