from django.db import IntegrityError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from config.test_helpers import AuthTestHelper
from library.models import Author, Genre, Serie


class AuthorListViewTest(AuthTestHelper, APITestCase):
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


class AuthorRetrieveViewTest(AuthTestHelper, APITestCase):
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


class SeriesListViewTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.serie = Serie.objects.create(name="Series One", description="Desc one")

    def test_get_list_returns_200(self):
        resp = self.client.get("/api/series/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 1)


class SeriesRetrieveViewTest(AuthTestHelper, APITestCase):
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


class AuthorNameUniqueTest(TestCase):
    def test_duplicate_author_name_raises_integrity_error(self):
        Author.objects.create(name="Jane Austen")
        with self.assertRaises(IntegrityError):
            Author.objects.create(name="Jane Austen")


class GenreListViewTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()

        cls.genre = Genre.objects.create(name="Fantasy")

    def test_get_list_returns_200_with_array(self):
        resp = self.client.get("/api/genres/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsInstance(resp.data, list)
        self.assertGreaterEqual(len(resp.data), 1)

    def test_get_list_sorted_alphabetically(self):

        Genre.objects.create(name="Adventure")
        resp = self.client.get("/api/genres/")
        names = [g["name"] for g in resp.data]
        self.assertEqual(names, sorted(names))


class GenreRetrieveViewTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()

        cls.genre = Genre.objects.create(name="Horror")

    def test_get_detail_returns_200(self):
        resp = self.client.get(f"/api/genres/{self.genre.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["name"], "Horror")

    def test_get_nonexistent_returns_404(self):
        resp = self.client.get("/api/genres/99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
