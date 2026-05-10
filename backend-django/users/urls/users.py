from django.urls import path

from users.views import (
    FollowListView,
    UserFollowView,
    UserProfileView,
    UserSettingsView,
    UserVisibilityView,
)

urlpatterns = [
    path("me/", UserSettingsView.as_view()),
    path("me/visibility/", UserVisibilityView.as_view()),
    path("<str:username>/", UserProfileView.as_view()),
    path("<str:username>/follow/", UserFollowView.as_view()),
    path(
        "<str:username>/followers/",
        FollowListView.as_view(follower_view=True),
    ),
    path(
        "<str:username>/following/",
        FollowListView.as_view(follower_view=False),
    ),
]
