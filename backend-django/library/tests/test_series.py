from rest_framework import status
from rest_framework.test import APITestCase

from library.models import Serie


class SerieListEmptyTest(APITestCase):
    """GET /api/series/ — empty database."""

    def test_list_returns_paginated_empty(self):
        resp = self.client.get("/api/series/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["data"], [])
        self.assertEqual(resp.data["page"], 1)
        self.assertEqual(resp.data["per_page"], 20)
        self.assertEqual(resp.data["total"], 0)


class SerieAPITests(APITestCase):
    """GET /api/series/ and /api/series/{id}/ — with data."""

    @classmethod
    def setUpTestData(cls):
        cls.serie = Serie.objects.create(
            name="The Lord of the Rings",
            description="Epic high-fantasy trilogy.",
            status=Serie.Status.COMPLETED,
        )

    def test_list_returns_paginated_data(self):
        resp = self.client.get("/api/series/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["total"], 1)
        self.assertEqual(len(resp.data["data"]), 1)
        self.assertEqual(resp.data["data"][0]["name"], "The Lord of the Rings")
        self.assertEqual(resp.data["data"][0]["description"], "Epic high-fantasy trilogy.")
        self.assertEqual(resp.data["data"][0]["status"], "COMPLETED")
        self.assertIn("created_at", resp.data["data"][0])

    def test_detail_existing_returns_200_with_all_fields(self):
        resp = self.client.get(f"/api/series/{self.serie.pk}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["name"], "The Lord of the Rings")
        self.assertEqual(resp.data["description"], "Epic high-fantasy trilogy.")
        self.assertEqual(resp.data["status"], "COMPLETED")

    def test_detail_nonexistent_returns_404(self):
        resp = self.client.get("/api/series/9999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
