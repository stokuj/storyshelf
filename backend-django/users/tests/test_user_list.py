from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from users.models import User


class UserListViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.alice = User.objects.create_user(
            email="alice@test.com", handle="alice", password="pass123",
            display_name="Alice A", profile_public=True,
        )
        self.bob = User.objects.create_user(
            email="bob@test.com", handle="bob", password="pass123",
            display_name="Bob B", profile_public=True,
        )
        self.hidden = User.objects.create_user(
            email="hidden@test.com", handle="hidden", password="pass123",
            profile_public=False,
        )

    def test_lists_only_public_profiles(self):
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        handles = [u["handle"] for u in response.data["data"]]
        self.assertIn("alice", handles)
        self.assertIn("bob", handles)
        self.assertNotIn("hidden", handles)

    def test_pagination_envelope_shape(self):
        response = self.client.get("/api/users/")
        self.assertEqual(set(response.data.keys()), {"data", "page", "per_page", "total"})
        self.assertEqual(response.data["total"], 2)

    def test_default_ordering_newest_first(self):
        response = self.client.get("/api/users/")
        handles = [u["handle"] for u in response.data["data"]]
        # hidden is newest but private; among public, bob created after alice.
        self.assertEqual(handles[0], "bob")

    def test_ordering_by_handle(self):
        response = self.client.get("/api/users/?ordering=handle")
        handles = [u["handle"] for u in response.data["data"]]
        self.assertEqual(handles, ["alice", "bob"])

    def test_search_by_handle(self):
        response = self.client.get("/api/users/?search=ali")
        handles = [u["handle"] for u in response.data["data"]]
        self.assertEqual(handles, ["alice"])

    def test_search_by_display_name(self):
        response = self.client.get("/api/users/?search=Bob B")
        handles = [u["handle"] for u in response.data["data"]]
        self.assertEqual(handles, ["bob"])

    def test_anonymous_access_allowed(self):
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
