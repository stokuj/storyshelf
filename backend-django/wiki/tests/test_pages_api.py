from rest_framework import status
from rest_framework.test import APITestCase

from config.test_helpers import AuthTestHelper
from users.models import User
from wiki import services
from wiki.models import Page

URL = "/api/wiki/pages/"
SOLARIS = f"{URL}books/solaris.md"


class PagesAPITest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.other = User.objects.create_user(
            email="other@test.com", handle="other", password="password123"
        )

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def create(self, **data):
        return self.client.post(URL, data, format="json")

    def edit(self, url, content, base_version):
        return self.client.put(
            url, {"content": content, "base_version": base_version}, format="json"
        )

    # Create

    def test_create_book_returns_template_page_with_created_version(self):
        resp = self.create(type="book", title="Solaris", author="Stanisław Lem", year=1961)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(resp.data["path"], "/books/solaris.md")
        self.assertIn("status: draft", resp.data["content"])
        self.assertIn("## Wątki i motywy", resp.data["content"])
        page = Page.objects.get(owner=self.user, path="/books/solaris.md")
        version = page.versions.get()
        self.assertEqual((version.kind, version.author), ("created", "human"))
        self.assertEqual(resp.data["version"], version.id)

    def test_create_slugs_polish_title(self):
        resp = self.create(type="book", title="Krew elfów")
        self.assertEqual(resp.data["path"], "/books/krew-elfow.md")

    def test_create_without_type_returns_400_on_type(self):
        resp = self.create(title="Solaris")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("type", resp.data)

    def test_create_with_unknown_type_returns_400_on_type(self):
        resp = self.create(type="author", title="Lem")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("type", resp.data)

    def test_create_existing_path_returns_409(self):
        self.create(type="book", title="Solaris")
        resp = self.create(type="book", title="Solaris")
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(resp.data["detail"], "Page already exists: /books/solaris.md")
        self.assertEqual(Page.objects.filter(owner=self.user).count(), 1)

    def test_create_character_needs_existing_book(self):
        resp = self.create(type="character", title="Snaut", book="/books/solaris.md")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("book", resp.data)
        self.create(type="book", title="Solaris")
        resp = self.create(type="character", title="Snaut", book="/books/solaris.md")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(resp.data["path"], "/characters/snaut--solaris.md")
        self.assertEqual(resp.data["book"], "/books/solaris.md")

    def test_create_character_without_book_returns_400(self):
        resp = self.create(type="character", title="Snaut")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("book", resp.data)

    def test_create_book_with_unknown_universe_returns_400(self):
        resp = self.create(type="book", title="Krew elfów", universe="/universes/wiedzmin.md")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("universe", resp.data)

    # List and read

    def test_list_filters_by_type_and_hides_content(self):
        self.create(type="book", title="Solaris")
        self.create(type="universe", title="Wiedźmin")
        services.create_page(self.other, "book", "Lalka")
        resp = self.client.get(URL, {"type": "book"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual([p["path"] for p in resp.data], ["/books/solaris.md"])
        self.assertNotIn("content", resp.data[0])
        self.assertEqual(len(self.client.get(URL).data), 2)

    def test_get_page_returns_content_and_version(self):
        created = self.create(type="book", title="Solaris").data
        resp = self.client.get(SOLARIS)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["content"], created["content"])
        self.assertEqual(resp.data["version"], created["version"])

    # Edit and versions

    def test_edit_adds_version_and_updates_title_but_not_path(self):
        page = self.create(type="book", title="Solaris").data
        content = page["content"].replace("title: Solaris", "title: Solaris (1961)")
        resp = self.edit(SOLARIS, content, page["version"])
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertEqual(resp.data["title"], "Solaris (1961)")
        self.assertEqual(resp.data["path"], "/books/solaris.md")
        self.assertNotEqual(resp.data["version"], page["version"])
        versions = self.client.get(f"{SOLARIS}/versions/").data
        self.assertEqual(versions["total"], 2)
        self.assertEqual([v["kind"] for v in versions["data"]], ["edit", "created"])

    def test_edit_stores_content_byte_for_byte(self):
        page = self.create(type="book", title="Solaris").data
        content = page["content"] + "\n## Ciekawostki\n\n  "
        self.edit(SOLARIS, content, page["version"])
        self.assertEqual(Page.objects.get(owner=self.user).content, content)

    def test_edit_without_template_heading_returns_400(self):
        page = self.create(type="book", title="Solaris").data
        resp = self.edit(SOLARIS, page["content"].replace("## Postacie\n", ""), page["version"])
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data, {"content": ["Missing template headings: Postacie"]})
        self.assertEqual(Page.objects.get(owner=self.user).versions.count(), 1)

    def test_edit_changing_type_returns_400(self):
        page = self.create(type="book", title="Solaris").data
        content = page["content"].replace("type: book", "type: universe")
        resp = self.edit(SOLARIS, content, page["version"])
        self.assertEqual(resp.data, {"content": ["Page type can't change"]})

    def test_stale_base_version_returns_409_and_changes_nothing(self):
        page = self.create(type="book", title="Solaris").data
        first = page["content"] + "\nPierwsza zmiana.\n"
        self.edit(SOLARIS, first, page["version"])
        resp = self.edit(SOLARIS, page["content"] + "\nDruga zmiana.\n", page["version"])
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        stored = Page.objects.get(owner=self.user)
        self.assertEqual(stored.content, first)
        self.assertEqual(stored.versions.count(), 2)

    # Access

    def test_other_users_page_returns_404(self):
        services.create_page(self.other, "book", "Lalka")
        url = f"{URL}books/lalka.md"
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.edit(url, "x", 1).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            self.client.get(f"{url}/versions/").status_code, status.HTTP_404_NOT_FOUND
        )

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(URL).status_code, status.HTTP_401_UNAUTHORIZED)
