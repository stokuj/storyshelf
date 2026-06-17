from unittest import mock

from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.throttling import ScopedRateThrottle

from books.models import Book
from characters.views import GenerateCharactersView
from users.models import User


# The character_generate scope is the cost-control for paid OpenRouter calls.
# Patch the view with a throttle carrying a hardcoded rate (throttling is
# disabled globally under test, and override_settings does not re-apply
# reliably across test classes).
class _GenerateThrottle(ScopedRateThrottle):
    THROTTLE_RATES = {"character_generate": "1/min"}


class CharacterGenerateThrottleTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            email="u@e.test", handle="u", password="password123"
        )
        self.book = Book.objects.create(title="T", slug="t")

    def tearDown(self):
        cache.clear()

    @mock.patch.object(GenerateCharactersView, "throttle_classes", [_GenerateThrottle])
    def test_generate_429_after_limit(self):
        self.client.force_authenticate(self.user)
        url = f"/api/books/{self.book.slug}/characters/generate/"
        first = self.client.post(url)
        self.assertNotEqual(first.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        second = self.client.post(url)
        self.assertEqual(second.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
