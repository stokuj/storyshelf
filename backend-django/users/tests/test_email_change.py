from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from config.test_helpers import AuthTestHelper

User = get_user_model()

USER_PASSWORD = "password123"


class EmailChangeTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()

    def test_change_email_returns_204(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(
            "/api/users/me/email/",
            {"new_email": "new@test.com", "current_password": USER_PASSWORD},
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_change_email_updates_db(self):
        self.client.force_authenticate(user=self.user)
        self.client.patch(
            "/api/users/me/email/",
            {"new_email": "updated@test.com", "current_password": USER_PASSWORD},
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "updated@test.com")

    def test_change_email_normalises_to_lowercase(self):
        self.client.force_authenticate(user=self.user)
        self.client.patch(
            "/api/users/me/email/",
            {"new_email": "Upper@TEST.com", "current_password": USER_PASSWORD},
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "upper@test.com")

    def test_change_email_wrong_password_returns_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(
            "/api/users/me/email/",
            {"new_email": "new@test.com", "current_password": "wrongpassword"},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_email_duplicate_returns_400(self):
        User.objects.create_user(email="taken@test.com", handle="takenuser", password="pw123456")
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(
            "/api/users/me/email/",
            {"new_email": "taken@test.com", "current_password": USER_PASSWORD},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_change_email_sends_notification_to_old_address(self):
        old_email = self.user.email
        self.client.force_authenticate(user=self.user)
        self.client.patch(
            "/api/users/me/email/",
            {"new_email": "new@test.com", "current_password": USER_PASSWORD},
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(old_email, mail.outbox[0].recipients())
