import importlib
import os
from unittest import mock

from django.test import SimpleTestCase


class ProdAllowedHostsTests(SimpleTestCase):
    def test_domain_appended_to_allowed_hosts(self):
        env = {
            "DJANGO_ENV": "prod",
            "DJANGO_SECRET_KEY": "x" * 50,
            "DOMAIN": "storyshelf.example.com",
            "ALLOWED_HOSTS": "localhost,127.0.0.1",
            "CSRF_TRUSTED_ORIGINS": "https://storyshelf.example.com",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            from config.settings import prod

            importlib.reload(prod)
            self.assertIn("storyshelf.example.com", prod.ALLOWED_HOSTS)
