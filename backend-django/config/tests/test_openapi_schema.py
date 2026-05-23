"""Snapshot test kontraktu API.

Test generuje schemat OpenAPI in-process przez drf-spectacular i porownuje
z plikiem `docs/api/openapi.yml` zacommittowanym w repo. PR ktory zmienia
API musi rownoczesnie zaktualizowac snapshot, inaczej CI faila.

Regeneracja po zmianie API:
    make regenerate-openapi
"""
from __future__ import annotations

from pathlib import Path

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SNAPSHOT_PATH = REPO_ROOT / "docs" / "api" / "openapi.yml"


class OpenAPISchemaSnapshotTest(TestCase):
    """Wykrywa nieintencjonalne zmiany kontraktu API."""

    def test_generated_schema_matches_snapshot(self):
        self.assertTrue(
            SNAPSHOT_PATH.exists(),
            f"Brak snapshotu OpenAPI w {SNAPSHOT_PATH}. "
            f"Wygeneruj go: `make regenerate-openapi`.",
        )

        client = APIClient()
        url = reverse("schema")
        response = client.get(url, HTTP_ACCEPT="application/vnd.oai.openapi")
        self.assertEqual(response.status_code, 200, response.content[:500])

        generated = response.content.decode("utf-8")
        snapshot = SNAPSHOT_PATH.read_text(encoding="utf-8")

        if generated.strip() != snapshot.strip():
            self.fail(
                "Wygenerowany schemat OpenAPI rozni sie od snapshotu "
                f"({SNAPSHOT_PATH}).\n"
                "Jezeli zmiana jest zamierzona, zregeneruj snapshot:\n"
                "    make regenerate-openapi\n"
                "i zacommittuj rownoczesnie z PR-em zmieniajacym API."
            )
