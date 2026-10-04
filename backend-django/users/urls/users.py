from django.urls import path

from users.views import (
    AvatarUploadView,
    EmailChangeView,
    PasswordChangeView,
    UserMeView,
    UserSettingsView,
)

urlpatterns = [
    path("me/", UserMeView.as_view()),
    path("me/password/", PasswordChangeView.as_view()),
    path("me/email/", EmailChangeView.as_view()),
    path("me/avatar/", AvatarUploadView.as_view()),
    path("me/settings/", UserSettingsView.as_view()),
]
