import logging
from datetime import date

from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, serializers, status, views
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from users.cookie_auth import clear_jwt_cookies, set_jwt_cookies
from users.models import User, UserFollow
from users.serializers import (
    AccountDeleteSerializer,
    AvatarUploadSerializer,
    EmailChangeSerializer,
    FollowSerializer,
    LoginSerializer,
    PasswordChangeSerializer,
    RegisterSerializer,
    UserMePatchSerializer,
    UserMeSerializer,
    UserProfileSerializer,
    UserSettingsPatchSerializer,
)

logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    """Rejestracja nowego użytkownika. Pola: email, handle, password."""

    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer
    throttle_scope = "auth_register"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        response = Response(
            {"authenticated": True, "email": user.email, "handle": user.handle},
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
            {"authenticated": True, "email": user.email, "handle": user.handle}
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
    """Zwraca stan sesji: authenticated, email, handle. Używane do inicjalizacji auth w SPA."""

    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        if request.user.is_authenticated:
            return Response(
                {
                    "authenticated": True,
                    "email": request.user.email,
                    "handle": request.user.handle,
                }
            )
        return Response(
            {
                "authenticated": False,
                "email": None,
                "handle": None,
            }
        )


class UserMeView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_throttles(self):
        scope_map = {
            "PATCH": "user_handle_change",
            "DELETE": "user_delete",
        }
        if self.request.method in scope_map:
            self.throttle_scope = scope_map[self.request.method]
            return [ScopedRateThrottle()]
        return []

    def get(self, request):
        serializer = UserMeSerializer(request.user, context={"request": request})
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserMePatchSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserMeSerializer(request.user, context={"request": request}).data)

    def delete(self, request):
        serializer = AccountDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data["current_password"]):
            return Response(
                {"detail": "Invalid password."},
                status=status.HTTP_403_FORBIDDEN,
            )
        user.delete()
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_jwt_cookies(response)
        return response


class PasswordChangeView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)
    throttle_scope = "user_password_change"

    def patch(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data["current_password"]):
            return Response(
                {"current_password": ["Invalid password."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        for token in OutstandingToken.objects.filter(user=user):
            BlacklistedToken.objects.get_or_create(token=token)
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        refresh = RefreshToken.for_user(user)
        response = Response(status=status.HTTP_204_NO_CONTENT)
        set_jwt_cookies(response, refresh.access_token, refresh)
        return response


class EmailChangeView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)
    throttle_scope = "user_email_change"

    def patch(self, request):
        serializer = EmailChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data["current_password"]):
            return Response(
                {"current_password": ["Invalid password."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        old_email = user.email
        new_email = serializer.validated_data["new_email"]
        user.email = new_email
        user.save(update_fields=["email"])
        try:
            send_mail(
                subject="Your StoryShelf email has been changed",
                message=(
                    f"Your account email was changed to {new_email}."
                    " If this wasn't you, contact support."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[old_email],
                fail_silently=False,
            )
        except Exception:
            logger.warning("Failed to send email change notification to %s", old_email)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AvatarUploadView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = [MultiPartParser]

    def patch(self, request):
        serializer = AvatarUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        old_avatar = user.avatar if user.avatar else None
        user.avatar = serializer.validated_data["avatar"]
        user.save(update_fields=["avatar"])
        # Delete old avatar AFTER saving the new one (no gap without avatar).
        if old_avatar and old_avatar.name != user.avatar.name:
            old_avatar.delete(save=False)
        return Response(
            {"avatar_url": request.build_absolute_uri(user.avatar.url)}
        )


class UserSettingsView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        return Response({"profile_public": request.user.profile_public})

    def patch(self, request):
        serializer = UserSettingsPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.profile_public = serializer.validated_data["profile_public"]
        user.save(update_fields=["profile_public"])
        return Response({"profile_public": user.profile_public})


class DataExportView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)
    throttle_scope = "user_data_export"

    def post(self, request):
        from users.exporters import build_user_export_zip

        data = build_user_export_zip(request.user)
        filename = f"storyshelf-export-{request.user.handle}-{date.today().isoformat()}.zip"
        response = HttpResponse(data, content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class UserProfileView(generics.RetrieveAPIView):
    """
    Publiczny profil użytkownika po handle. Zwraca 404 jeśli profil jest prywatny
    i requestujący nie jest właścicielem.
    """

    permission_classes = (permissions.AllowAny,)
    serializer_class = UserProfileSerializer
    lookup_field = "handle"
    queryset = User.objects.all()

    def get_object(self):
        user = super().get_object()
        if not user.profile_public and user != self.request.user:
            raise Http404("No User matches the given query.")
        return user


class UserFollowView(views.APIView):
    """
    POST: Obserwuj użytkownika o podanym handle.
          400 jeśli próba obserwowania siebie, 409 jeśli już obserwujesz.
    DELETE: Przestań obserwować. 404 jeśli relacja nie istnieje.
    """

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, handle):
        target = get_object_or_404(User, handle=handle)
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
        return Response(FollowSerializer(follow).data, status=status.HTTP_201_CREATED)

    def delete(self, request, handle):
        target = get_object_or_404(User, handle=handle)
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
    Płaska lista obserwujących lub obserwowanych dla użytkownika o podanym handle.
    follower_view=True → kto obserwuje tego użytkownika; False → kogo ten użytkownik obserwuje.
    """

    permission_classes = (permissions.AllowAny,)
    serializer_class = FollowSerializer
    pagination_class = None
    follower_view = False

    def get_queryset(self):
        handle = self.kwargs["handle"]
        user = get_object_or_404(User, handle=handle)
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


