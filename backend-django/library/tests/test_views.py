from rest_framework import status
from rest_framework.test import APITestCase

from config.test_helpers import AuthTestHelper
from library.models import Author, Serie


class AuthorListCreateTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.author1 = Author.objects.create(name="Author One", bio="Bio one")

    def test_get_list_returns_200(self):
        resp = self.client.get("/api/authors/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 1)

    def test_get_list_empty_returns_200(self):
        Author.objects.all().delete()
        resp = self.client.get("/api/authors/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    def test_post_create_author_as_admin_returns_201(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(
            "/api/authors/",
            {
                "name": "New Author",
                "bio": "New bio",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Author.objects.filter(name="New Author").exists())

    def test_post_create_author_as_user_returns_403(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post("/api/authors/", {"name": "Hack Author"})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_create_author_unauthenticated_returns_401(self):
        resp = self.client.post("/api/authors/", {"name": "No Auth"})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_create_author_missing_name_returns_400(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post("/api/authors/", {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class AuthorDetailTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.author = Author.objects.create(name="Detail Author", bio="Detail bio")

    def test_get_detail_returns_200(self):
        resp = self.client.get(f"/api/authors/{self.author.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["name"], "Detail Author")

    def test_get_nonexistent_returns_404(self):
        resp = self.client.get("/api/authors/99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_update_as_admin_returns_200(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.put(
            f"/api/authors/{self.author.id}/",
            {"name": "Updated Author", "bio": "Updated bio"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.author.refresh_from_db()
        self.assertEqual(self.author.name, "Updated Author")

    def test_delete_as_admin_returns_204(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.delete(f"/api/authors/{self.author.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Author.objects.filter(id=self.author.id).exists())

    def test_delete_as_user_returns_403(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete(f"/api/authors/{self.author.id}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class SeriesListCreateTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.serie = Serie.objects.create(name="Series One", description="Desc one")

    def test_get_list_returns_200(self):
        resp = self.client.get("/api/series/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 1)

    def test_post_create_series_as_admin_returns_201(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(
            "/api/series/",
            {
                "name": "New Series",
                "description": "A new one",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Serie.objects.filter(name="New Series").exists())

    def test_post_create_series_as_user_returns_403(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post("/api/series/", {"name": "Hack Series"})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_create_series_unauthenticated_returns_401(self):
        resp = self.client.post("/api/series/", {"name": "No Auth"})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_create_series_missing_name_returns_400(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post("/api/series/", {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class SeriesDetailTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.serie = Serie.objects.create(name="Detail Series", description="Detail")

    def test_get_detail_returns_200(self):
        resp = self.client.get(f"/api/series/{self.serie.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["name"], "Detail Series")

    def test_get_nonexistent_returns_404(self):
        resp = self.client.get("/api/series/99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_update_as_admin_returns_200(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.put(
            f"/api/series/{self.serie.id}/",
            {"name": "Updated Series", "description": "Updated"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.serie.refresh_from_db()
        self.assertEqual(self.serie.name, "Updated Series")

    def test_delete_as_admin_returns_204(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.delete(f"/api/series/{self.serie.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Serie.objects.filter(id=self.serie.id).exists())

    def test_delete_as_user_returns_403(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete(f"/api/series/{self.serie.id}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class AuthorResponseStructureTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.author = Author.objects.create(name="Struct Author")

    def test_author_response_has_avatar_url(self):
        resp = self.client.get(f"/api/authors/{self.author.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("avatar_url", resp.data)


class SeriesResponseStructureTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.serie = Serie.objects.create(name="Struct Series")

    def test_series_response_has_cover_url(self):
        resp = self.client.get(f"/api/series/{self.serie.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("cover_url", resp.data)
