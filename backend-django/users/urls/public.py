from django.urls import path

from users.views import FollowListView, UserFollowView, UserProfileView

urlpatterns = [
    path("<str:handle>/follow/", UserFollowView.as_view()),
    path("<str:handle>/followers/", FollowListView.as_view(follower_view=True)),
    path("<str:handle>/following/", FollowListView.as_view(follower_view=False)),
    path("<str:handle>/", UserProfileView.as_view()),
]
