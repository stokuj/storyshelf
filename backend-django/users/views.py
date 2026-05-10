from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User, UserFollow
from users.serializers import (
    FollowSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserProfileSerializer,
    UserSettingsSerializer,
)


class RegisterView(generics.CreateAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoginView(views.APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class LogoutView(views.APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except (TokenError, AttributeError):
            pass
        return Response({"message": "Logged out successfully"})


class AuthMeView(views.APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        if request.user.is_authenticated:
            return Response(
                {
                    "authenticated": True,
                    "email": request.user.email,
                    "username": request.user.username,
                    "role": request.user.role,
                }
            )
        return Response(
            {
                "authenticated": False,
                "email": None,
                "username": None,
                "role": None,
            }
        )


class UserProfileView(generics.RetrieveAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserProfileSerializer
    lookup_field = "username"
    queryset = User.objects.all()

    def get_object(self):
        user = super().get_object()
        if not user.profile_public and user != self.request.user:
            self.permission_denied(self.request)
        return user


class UserSettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSettingsSerializer

    def get_object(self):
        return self.request.user


class UserVisibilityView(views.APIView):
    def patch(self, request):
        public = request.query_params.get("profilePublic", "true").lower() == "true"
        request.user.profile_public = public
        request.user.save(update_fields=["profile_public"])
        return Response({"profile_public": request.user.profile_public})


class UserFollowView(views.APIView):
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
        follow = UserFollow.objects.create(follower=request.user, following=target)
        serializer = FollowSerializer(follow)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, username):
        target = get_object_or_404(User, username=username)
        follow = UserFollow.objects.filter(
            follower=request.user, following=target
        ).first()
        if not follow:
            return Response(
                {"detail": "You are not following this user"},
                status=status.HTTP_404_NOT_FOUND,
            )
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowListView(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = FollowSerializer
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
