from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase

from config.test_helpers import AuthTestHelper
from wiki.models import Page, PageVersion


def seed(email):
    out = StringIO()
    call_command("seed", email, stdout=out)
    return out.getvalue()


class SeedTest(AuthTestHelper, TestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()

    def test_loads_every_fixture_with_one_created_version(self):
        self.assertIn("created 15, skipped 0", seed("user@test.com"))
        self.assertEqual(Page.objects.filter(owner=self.user).count(), 15)
        self.assertEqual(
            PageVersion.objects.filter(page__owner=self.user, kind="created").count(), 15
        )
        geralt = Page.objects.get(owner=self.user, path="/characters/geralt--krew-elfow.md")
        self.assertEqual((geralt.type, geralt.book), ("character", "/books/krew-elfow.md"))

    def test_second_run_skips_existing_pages(self):
        seed("user@test.com")
        self.assertIn("created 0, skipped 15", seed("user@test.com"))
        self.assertEqual(PageVersion.objects.filter(page__owner=self.user).count(), 15)

    def test_unknown_email_fails(self):
        with self.assertRaises(CommandError):
            seed("nobody@test.com")
