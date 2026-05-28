from rest_framework import status
from rest_framework.test import APITestCase

from library.models import Tag


class TagListEmptyTest(APITestCase):
    """GET /api/tags/ — empty database."""

    def test_list_returns_paginated_empty(self):
        resp = self.client.get("/api/tags/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["data"], [])
        self.assertEqual(resp.data["page"], 1)
        self.assertEqual(resp.data["per_page"], 20)
        self.assertEqual(resp.data["total"], 0)


class TagAPITests(APITestCase):
    """GET /api/tags/ and /api/tags/{id}/ — with data."""

    @classmethod
    def setUpTestData(cls):
        cls.tag = Tag.objects.create(name="classic")

    def test_list_returns_paginated_data(self):
        resp = self.client.get("/api/tags/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["total"], 1)
        self.assertEqual(len(resp.data["data"]), 1)
        self.assertEqual(resp.data["data"][0]["name"], "classic")

    def test_detail_existing_returns_200_with_all_fields(self):
        resp = self.client.get(f"/api/tags/{self.tag.pk}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["name"], "classic")

    def test_detail_nonexistent_returns_404(self):
        resp = self.client.get("/api/tags/9999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
