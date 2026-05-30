from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from users.models import User


class PublicUserProfileViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            email="owner@test.com", handle="shelfowner", password="pass123",
            profile_public=True,
        )
        self.visitor = User.objects.create_user(
            email="visitor@test.com", handle="visitor", password="pass123"
        )

    def test_public_profile_visible_to_anon(self):
        response = self.client.get(f"/api/u/{self.owner.handle}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_private_profile_returns_404_for_visitor(self):
        self.owner.profile_public = False
        self.owner.save()
        self.client.force_authenticate(user=self.visitor)
        response = self.client.get(f"/api/u/{self.owner.handle}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_private_profile_owner_can_see_own_profile(self):
        self.owner.profile_public = False
        self.owner.save()
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f"/api/u/{self.owner.handle}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_nonexistent_handle_returns_404(self):
        response = self.client.get("/api/u/doesnotexist/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
