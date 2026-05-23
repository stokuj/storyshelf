from django.urls import path

from users.views import (
    AvatarUploadView,
    DataExportView,
    EmailChangeView,
    FollowListView,
    PasswordChangeView,
    PublicUserRecentlyReadView,
    PublicUserShelvesView,
    UserFollowView,
    UserMeView,
    UserSettingsView,
)

urlpatterns = [
    path("me/", UserMeView.as_view()),
    path("me/password/", PasswordChangeView.as_view()),
    path("me/email/", EmailChangeView.as_view()),
    path("me/avatar/", AvatarUploadView.as_view()),
    path("me/settings/", UserSettingsView.as_view()),
    path("me/export/", DataExportView.as_view()),
    path("<str:handle>/shelves/", PublicUserShelvesView.as_view()),
    path("<str:handle>/recently-read/", PublicUserRecentlyReadView.as_view()),
    path("<str:handle>/follow/", UserFollowView.as_view()),
    path("<str:handle>/followers/", FollowListView.as_view(follower_view=True)),
    path("<str:handle>/following/", FollowListView.as_view(follower_view=False)),
]
