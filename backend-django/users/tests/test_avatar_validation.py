import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from PIL import Image
from rest_framework import serializers

from users.serializers import AvatarUploadSerializer


def _img(fmt, content_type):
    buf = io.BytesIO()
    Image.new("RGB", (64, 64)).save(buf, format=fmt)
    buf.seek(0)
    ext = {"PNG": "png", "GIF": "gif"}[fmt]
    return SimpleUploadedFile(f"a.{ext}", buf.read(), content_type=content_type)


class AvatarValidationTests(SimpleTestCase):
    def test_png_accepted(self):
        s = AvatarUploadSerializer(data={"avatar": _img("PNG", "image/png")})
        self.assertTrue(s.is_valid(), s.errors)

    def test_gif_with_spoofed_jpeg_mime_rejected(self):
        s = AvatarUploadSerializer(data={"avatar": _img("GIF", "image/jpeg")})
        self.assertFalse(s.is_valid())
        self.assertIn("avatar", s.errors)

    def test_validate_avatar_rejects_disallowed_format_direct(self):
        # Valid GIF with content_type spoofed as JPEG. Old code trusted
        # content_type (in the allowlist) and accepted it; the Pillow img.format
        # check now rejects it. Calls the validator directly to bypass DRF's
        # ImageField, which rewrites content_type before our validator runs.
        buf = io.BytesIO()
        Image.new("RGB", (64, 64)).save(buf, format="GIF")
        buf.seek(0)
        f = SimpleUploadedFile("a.jpg", buf.read(), content_type="image/jpeg")
        with self.assertRaises(serializers.ValidationError):
            AvatarUploadSerializer().validate_avatar(f)
