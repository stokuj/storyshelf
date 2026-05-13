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
            username="targetuser",
            password="pw",
            bio="Hello world",
        )
        self.url = f"/api/users/{self.target.username}/"

    def test_get_public_profile_returns_200(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["username"], "targetuser")
        self.assertEqual(resp.data["bio"], "Hello world")

    def test_get_nonexistent_user_returns_404(self):
        resp = self.client.get("/api/users/nonexistent/")
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
        self.assertEqual(resp.data["username"], "testuser")
        self.assertIn("email", resp.data)
        self.assertIn("profilePublic", resp.data)

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


class UserVisibilityTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()

    def test_patch_visibility_to_false(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch("/api/users/me/visibility/?profilePublic=false")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["profile_public"])
        self.user.refresh_from_db()
        self.assertFalse(self.user.profile_public)

    def test_patch_visibility_to_true(self):
        self.user.profile_public = False
        self.user.save()
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch("/api/users/me/visibility/?profilePublic=true")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["profile_public"])

    def test_patch_visibility_unauthenticated_returns_401(self):
        resp = self.client.patch("/api/users/me/visibility/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class UserFollowTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()

    def setUp(self):
        self.target = User.objects.create_user(
            email="target2@test.com",
            username="target2",
            password="pw",
        )
        self.url = f"/api/users/{self.target.username}/follow/"

    def test_post_follow_returns_201(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["followerUsername"], "testuser")
        self.assertEqual(resp.data["followingUsername"], "target2")

    def test_post_follow_self_returns_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(f"/api/users/{self.user.username}/follow/")
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
            username="target3",
            password="pw",
        )

    def test_list_followers_returns_200(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(f"/api/users/{self.target.username}/follow/")
        resp = self.client.get(f"/api/users/{self.target.username}/followers/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["followerUsername"], "testuser")

    def test_list_following_returns_200(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(f"/api/users/{self.target.username}/follow/")
        resp = self.client.get("/api/users/testuser/following/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["followingUsername"], "target3")

    def test_list_followers_empty_returns_200(self):
        resp = self.client.get(f"/api/users/{self.target.username}/followers/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    def test_list_followers_nonexistent_user_returns_404(self):
        resp = self.client.get("/api/users/nobody/followers/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class UserSettingsResponseStructureTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()

    def test_response_uses_camelcase_keys(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/users/me/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("profilePublic", resp.data)
        self.assertIn("avatarUrl", resp.data)
        self.assertIn("memberSince", resp.data)
