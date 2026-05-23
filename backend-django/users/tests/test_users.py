from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from config.test_helpers import AuthTestHelper

User = get_user_model()


class UserProfileTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()

    def setUp(self):
        self.target = User.objects.create_user(
            email="target@test.com",
            handle="targetuser",
            password="pw",
            bio="Hello world",
        )
        self.url = f"/api/u/{self.target.handle}/"

    def test_get_public_profile_returns_200(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["handle"], "targetuser")
        self.assertEqual(resp.data["bio"], "Hello world")

    def test_get_nonexistent_user_returns_404(self):
        resp = self.client.get("/api/u/nonexistent/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_private_profile_returns_404_for_others(self):
        self.target.profile_public = False
        self.target.save()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_private_profile_returns_200_for_owner(self):
        self.target.profile_public = False
        self.target.save()
        self.client.force_authenticate(user=self.target)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class UserSettingsTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()

    def test_get_own_settings_returns_200(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/users/me/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["handle"], "testuser")
        self.assertIn("email", resp.data)
        self.assertIn("profile_public", resp.data["settings"])

    def test_get_settings_unauthenticated_returns_401(self):
        resp = self.client.get("/api/users/me/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_settings_updates_bio(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch("/api/users/me/", {"bio": "New bio"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["bio"], "New bio")
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, "New bio")


class UserFollowTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()

    def setUp(self):
        self.target = User.objects.create_user(
            email="target2@test.com",
            handle="target2",
            password="pw",
        )
        self.url = f"/api/users/{self.target.handle}/follow/"

    def test_post_follow_returns_201(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["follower_handle"], "testuser")
        self.assertEqual(resp.data["following_handle"], "target2")

    def test_post_follow_self_returns_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(f"/api/users/{self.user.handle}/follow/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_follow_already_following_returns_409(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(self.url)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

    def test_post_follow_unauthenticated_returns_401(self):
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_unfollow_returns_204(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(self.url)
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_unfollow_not_following_returns_404(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_follow_nonexistent_user_returns_404(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete("/api/users/nobody/follow/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class FollowListTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()

    def setUp(self):
        self.target = User.objects.create_user(
            email="target3@test.com",
            handle="target3",
            password="pw",
        )

    def test_list_followers_returns_200(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(f"/api/users/{self.target.handle}/follow/")
        resp = self.client.get(f"/api/users/{self.target.handle}/followers/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["follower_handle"], "testuser")

    def test_list_following_returns_200(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(f"/api/users/{self.target.handle}/follow/")
        resp = self.client.get("/api/users/testuser/following/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["following_handle"], "target3")

    def test_list_followers_empty_returns_200(self):
        resp = self.client.get(f"/api/users/{self.target.handle}/followers/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    def test_list_followers_nonexistent_user_returns_404(self):
        resp = self.client.get("/api/users/nobody/followers/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class UserSettingsResponseStructureTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()

    def test_response_uses_snake_case_keys(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/users/me/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("profile_public", resp.data["settings"])
        self.assertIn("avatar_url", resp.data)
        self.assertIn("member_since", resp.data)
