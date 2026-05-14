from django.urls import path

from users.views import AuthMeView, LoginView, LogoutView, RegisterView, TokenRefreshCookieView

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("login/", LoginView.as_view()),
    path("refresh/", TokenRefreshCookieView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("me/", AuthMeView.as_view()),
]
