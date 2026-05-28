from datetime import date

from rest_framework import status
from rest_framework.test import APITestCase

from library.models import Author


class AuthorListEmptyTest(APITestCase):
    """GET /api/authors/ — empty database."""

    def test_list_returns_paginated_empty(self):
        resp = self.client.get("/api/authors/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["data"], [])
        self.assertEqual(resp.data["page"], 1)
        self.assertEqual(resp.data["per_page"], 20)
        self.assertEqual(resp.data["total"], 0)


class AuthorAPITests(APITestCase):
    """GET /api/authors/ and /api/authors/{id}/ — with data."""

    @classmethod
    def setUpTestData(cls):
        cls.author = Author.objects.create(
            name="J.R.R. Tolkien",
            bio="English writer, poet, philologist, and academic.",
            birth_date=date(1892, 1, 3),
        )

    def test_list_returns_paginated_data(self):
        resp = self.client.get("/api/authors/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["total"], 1)
        self.assertEqual(len(resp.data["data"]), 1)
        self.assertEqual(resp.data["data"][0]["name"], "J.R.R. Tolkien")
        expected_bio = "English writer, poet, philologist, and academic."
        self.assertEqual(resp.data["data"][0]["bio"], expected_bio)
        self.assertEqual(resp.data["data"][0]["birth_date"], "1892-01-03")

    def test_detail_existing_returns_200_with_all_fields(self):
        resp = self.client.get(f"/api/authors/{self.author.pk}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["name"], "J.R.R. Tolkien")
        self.assertEqual(resp.data["bio"], "English writer, poet, philologist, and academic.")
        self.assertEqual(resp.data["birth_date"], "1892-01-03")

    def test_detail_nonexistent_returns_404(self):
        resp = self.client.get("/api/authors/9999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
