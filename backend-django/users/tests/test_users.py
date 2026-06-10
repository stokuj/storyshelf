from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from config.test_helpers import AuthTestHelper
from users.serializers import RegisterSerializer

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
            profile_public=True,
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

    def test_profile_includes_follow_counts_and_is_following(self):
        # self.user follows self.target → target has 1 follower, 0 following
        self.client.force_authenticate(user=self.user)
        follow_resp = self.client.post(f"/api/u/{self.target.handle}/follow/")
        self.assertEqual(follow_resp.status_code, status.HTTP_201_CREATED)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["followers_count"], 1)
        self.assertEqual(resp.data["following_count"], 0)
        self.assertTrue(resp.data["is_following"])

    def test_profile_is_following_false_for_non_follower(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(self.url)
        self.assertFalse(resp.data["is_following"])
        self.assertEqual(resp.data["followers_count"], 0)
        self.assertEqual(resp.data["following_count"], 0)

    def test_profile_is_following_false_for_anon(self):
        resp = self.client.get(self.url)
        self.assertFalse(resp.data["is_following"])

    def test_profile_is_following_false_on_own_profile(self):
        self.client.force_authenticate(user=self.target)
        resp = self.client.get(self.url)
        self.assertFalse(resp.data["is_following"])


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
        self.assertIn("profile_public", resp.data)

    def test_get_settings_unauthenticated_returns_401(self):
        resp = self.client.get("/api/users/me/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_settings_empty_body_returns_200_noop(self):
        # Regression: empty PATCH must not raise KeyError -> 500.
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch("/api/users/me/settings/", {})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("profile_public", resp.data)

    def test_patch_settings_toggles_profile_public(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch("/api/users/me/settings/", {"profile_public": True})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["profile_public"])

    def test_register_serializer_rejects_weak_password(self):
        # Regression: registration must run Django password validators.
        # "abc123" fails both the field's min_length=8 and Django's
        # MinimumLengthValidator (8); the latter only runs via validate_password.
        serializer = RegisterSerializer(
            data={"email": "weak@test.com", "handle": "weakpwuser", "password": "abc123"}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

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
        self.url = f"/api/u/{self.target.handle}/follow/"

    def test_post_follow_returns_201(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["follower_handle"], "testuser")
        self.assertEqual(resp.data["following_handle"], "target2")

    def test_post_follow_self_returns_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(f"/api/u/{self.user.handle}/follow/")
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
        resp = self.client.delete("/api/u/nobody/follow/")
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
            profile_public=True,
        )

    def test_list_followers_returns_200(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(f"/api/u/{self.target.handle}/follow/")
        resp = self.client.get(f"/api/u/{self.target.handle}/followers/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["handle"], "testuser")
        self.assertEqual(resp.data[0]["display_name"], self.user.display_name)
        self.assertIn("avatar_url", resp.data[0])
        self.assertIn("followed_at", resp.data[0])

    def test_list_following_returns_200(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(f"/api/u/{self.target.handle}/follow/")
        resp = self.client.get("/api/u/testuser/following/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["handle"], "target3")
        self.assertEqual(resp.data[0]["display_name"], self.target.display_name)

    def test_list_followers_empty_returns_200(self):
        resp = self.client.get(f"/api/u/{self.target.handle}/followers/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    def test_list_followers_nonexistent_user_returns_404(self):
        resp = self.client.get("/api/u/nobody/followers/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_followers_private_profile_returns_404(self):
        private = User.objects.create_user(
            email="priv@test.com", handle="privuser", password="pw"
        )
        resp = self.client.get(f"/api/u/{private.handle}/followers/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class UserSettingsResponseStructureTest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()

    def test_response_uses_snake_case_keys(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/users/me/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("profile_public", resp.data)
        self.assertIn("avatar_url", resp.data)
        self.assertIn("member_since", resp.data)
