from django.urls import path

from users.views import (
    AvatarUploadView,
    DataExportView,
    EmailChangeView,
    MyStatsView,
    PasswordChangeView,
    UserListView,
    UserMeView,
    UserSettingsView,
)

urlpatterns = [
    path("", UserListView.as_view()),
    path("me/", UserMeView.as_view()),
    path("me/password/", PasswordChangeView.as_view()),
    path("me/email/", EmailChangeView.as_view()),
    path("me/avatar/", AvatarUploadView.as_view()),
    path("me/settings/", UserSettingsView.as_view()),
    path("me/export/", DataExportView.as_view()),
    path("me/stats/", MyStatsView.as_view()),
]
