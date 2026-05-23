import io

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from config.test_helpers import AuthTestHelper

User = get_user_model()


def _make_image_bytes(width=100, height=100, fmt="JPEG"):
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color=(100, 150, 200)).save(buf, format=fmt)
    content_type_map = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
    ext_map = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}
    return SimpleUploadedFile(
        name=f"avatar.{ext_map.get(fmt, 'jpg')}",
        content=buf.getvalue(),
        content_type=content_type_map.get(fmt, "image/jpeg"),
    )


@override_settings(MEDIA_ROOT="/tmp/storyshelf-test-media")
class AvatarUploadTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()

    def setUp(self):
        super().setUp()
        self.user.refresh_from_db()

    def _upload(self, image_bytes):
        return self.client.patch(
            "/api/users/me/avatar/",
            {"avatar": image_bytes},
            format="multipart",
        )

    def test_upload_jpeg_returns_200_with_avatar_url(self):
        self.client.force_authenticate(user=self.user)
        resp = self._upload(_make_image_bytes())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("avatar_url", resp.data)
        self.assertIn("/media/avatars/", resp.data["avatar_url"])

    def test_upload_png_accepted(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(
            "/api/users/me/avatar/",
            {"avatar": _make_image_bytes(fmt="PNG")},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_upload_exceeds_dimensions_returns_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(
            "/api/users/me/avatar/",
            {"avatar": _make_image_bytes(2000, 2000)},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_unauthenticated_returns_401(self):
        resp = self._upload(_make_image_bytes())
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
