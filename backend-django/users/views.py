from django.db import IntegrityError
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, serializers, status, views
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from users.cookie_auth import clear_jwt_cookies, set_jwt_cookies
from users.models import User, UserFollow
from users.serializers import (
    FollowSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserProfileSerializer,
    UserSettingsSerializer,
)


class RegisterView(generics.CreateAPIView):
    """Rejestracja nowego użytkownika. Pola: email, username, password."""

    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer
    throttle_scope = "auth_register"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        response = Response(
            {"authenticated": True, "email": user.email, "username": user.username},
            status=status.HTTP_201_CREATED,
        )
        set_jwt_cookies(response, refresh.access_token, refresh)
        return response


class LoginView(views.APIView):
    """Logowanie. Ustawia HttpOnly cookies. Pola: email, password."""

    permission_classes = (permissions.AllowAny,)
    throttle_scope = "auth_login"

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        response = Response(
            {"authenticated": True, "email": user.email, "username": user.username}
        )
        set_jwt_cookies(response, refresh.access_token, refresh)
        return response


class TokenRefreshCookieView(views.APIView):
    """Odświeża access token z HttpOnly refresh cookie. Ustawia nowe cookies."""

    permission_classes = (permissions.AllowAny,)
    throttle_scope = "auth_refresh"

    def post(self, request):
        raw_refresh = request.COOKIES.get("refresh_token")
        if not raw_refresh:
            return Response(
                {"detail": "Refresh token not found."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        serializer = TokenRefreshSerializer(data={"refresh": raw_refresh})
        try:
            serializer.is_valid(raise_exception=True)
        except (TokenError, serializers.ValidationError):
            return Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        response = Response({"authenticated": True})
        new_refresh = serializer.validated_data.get("refresh")
        set_jwt_cookies(response, serializer.validated_data["access"], new_refresh)
        return response


class LogoutView(views.APIView):
    """Wylogowanie. Czyści cookies i blacklistuje refresh token."""

    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        raw_refresh = request.COOKIES.get("refresh_token")
        if raw_refresh:
            try:
                token = RefreshToken(raw_refresh)
                token.blacklist()
            except (TokenError, AttributeError):
                pass
        response = Response({"message": "Logged out successfully"})
        clear_jwt_cookies(response)
        return response


class AuthMeView(views.APIView):
    """Zwraca stan sesji: authenticated, email, username. Używane do inicjalizacji auth w SPA."""

    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        if request.user.is_authenticated:
            return Response(
                {
                    "authenticated": True,
                    "email": request.user.email,
                    "username": request.user.username,
                }
            )
        return Response(
            {
                "authenticated": False,
                "email": None,
                "username": None,
            }
        )


class UserProfileView(generics.RetrieveAPIView):
    """
    Publiczny profil użytkownika po username. Zwraca 404 jeśli profil jest prywatny
    i requestujący nie jest właścicielem.
    """

    permission_classes = (permissions.AllowAny,)
    serializer_class = UserProfileSerializer
    lookup_field = "username"
    queryset = User.objects.all()

    def get_object(self):
        user = super().get_object()
        if not user.profile_public and user != self.request.user:
            raise Http404("No User matches the given query.")
        return user


class UserSettingsView(generics.RetrieveUpdateAPIView):
    """GET/PUT/PATCH ustawień zalogowanego użytkownika: username, bio, avatar_url."""

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSettingsSerializer

    def get_object(self):
        return self.request.user


class UserVisibilityView(views.APIView):
    """PATCH ?profilePublic=true|false — przełącza widoczność profilu zalogowanego użytkownika."""

    permission_classes = (permissions.IsAuthenticated,)

    def patch(self, request):
        public = request.query_params.get("profilePublic", "true").lower() == "true"
        request.user.profile_public = public
        request.user.save(update_fields=["profile_public"])
        return Response({"profile_public": request.user.profile_public})


class UserFollowView(views.APIView):
    """
    POST: Obserwuj użytkownika o podanym username.
          400 jeśli próba obserwowania siebie, 409 jeśli już obserwujesz.
    DELETE: Przestań obserwować. 404 jeśli relacja nie istnieje.
    """

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, username):
        target = get_object_or_404(User, username=username)
        if target == request.user:
            return Response(
                {"detail": "You cannot follow yourself"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if UserFollow.objects.filter(follower=request.user, following=target).exists():
            return Response(
                {"detail": "Already following this user"},
                status=status.HTTP_409_CONFLICT,
            )
        try:
            follow = UserFollow.objects.create(follower=request.user, following=target)
        except IntegrityError:
            return Response(
                {"detail": "Already following this user"},
                status=status.HTTP_409_CONFLICT,
            )
        serializer = FollowSerializer(follow)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, username):
        target = get_object_or_404(User, username=username)
        follow = UserFollow.objects.filter(follower=request.user, following=target).first()
        if not follow:
            return Response(
                {"detail": "You are not following this user"},
                status=status.HTTP_404_NOT_FOUND,
            )
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowListView(generics.ListAPIView):
    """
    Płaska lista obserwujących lub obserwowanych dla użytkownika o podanym username.
    follower_view=True → kto obserwuje tego użytkownika; False → kogo ten użytkownik obserwuje.
    """

    permission_classes = (permissions.AllowAny,)
    serializer_class = FollowSerializer
    pagination_class = None
    follower_view = False

    def get_queryset(self):
        username = self.kwargs["username"]
        user = get_object_or_404(User, username=username)
        if self.follower_view:
            return (
                UserFollow.objects.filter(following=user)
                .select_related("follower")
                .order_by("-followed_at")
            )
        return (
            UserFollow.objects.filter(follower=user)
            .select_related("following")
            .order_by("-followed_at")
        )
