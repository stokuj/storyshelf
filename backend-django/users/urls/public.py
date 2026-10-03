from django.urls import path

from users.views import UserProfileView

urlpatterns = [
    path("<str:handle>/", UserProfileView.as_view()),
]
