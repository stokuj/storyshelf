from unittest import mock

from django.core.cache import cache
from rest_framework.test import APITestCase
from rest_framework.throttling import ScopedRateThrottle

from users.views import RegisterView


# Throttling is disabled globally under test (settings/dev.py), and overriding
# DEFAULT_THROTTLE_* via override_settings does not re-apply reliably across test
# classes (DRF resolves throttle classes once). Patch the view with a throttle
# carrying a hardcoded rate instead — self-contained and order-independent.
class _RegisterThrottle(ScopedRateThrottle):
    THROTTLE_RATES = {"auth_register": "2/min"}


class RegisterThrottleTests(APITestCase):
    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def _body(self, n):
        return {
            "email": f"u{n}@e.test",
            "handle": f"u{n}",
            "password": "password123",
            "display_name": "U",
        }

    @mock.patch.object(RegisterView, "throttle_classes", [_RegisterThrottle])
    def test_register_429_after_limit(self):
        r1 = self.client.post("/api/auth/register/", self._body(1), format="json")
        self.client.post("/api/auth/register/", self._body(2), format="json")
        r3 = self.client.post("/api/auth/register/", self._body(3), format="json")
        self.assertNotEqual(r1.status_code, 429)
        self.assertEqual(r3.status_code, 429)
