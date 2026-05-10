from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from users.views import AuthMeView, LoginView, LogoutView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("login/", LoginView.as_view()),
    path("refresh/", TokenRefreshView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("me/", AuthMeView.as_view()),
]
