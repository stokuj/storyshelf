from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User, UserFollow


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(min_length=6, max_length=72, write_only=True)
    username = serializers.RegexField(
        regex=r"^[a-z]{3,30}$",
        max_length=30,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )

    class Meta:
        model = User
        fields = ("email", "username", "password")

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            email=attrs["email"],
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError("Invalid email or password")
        if not user.is_active:
            raise serializers.ValidationError("Account is deactivated")
        attrs["user"] = user
        return attrs

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance["user"])
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


class UserProfileSerializer(serializers.ModelSerializer):
    memberSince = serializers.DateTimeField(source="created_at", read_only=True)
    avatarUrl = serializers.URLField(source="avatar_url", read_only=True)

    class Meta:
        model = User
        fields = ("username", "bio", "avatarUrl", "memberSince")
        read_only_fields = ("username", "bio", "avatarUrl", "memberSince")


class UserSettingsSerializer(serializers.ModelSerializer):
    memberSince = serializers.DateTimeField(source="created_at", read_only=True)
    avatarUrl = serializers.URLField(source="avatar_url", required=False, allow_blank=True)
    profilePublic = serializers.BooleanField(source="profile_public")

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "bio",
            "avatarUrl",
            "profilePublic",
            "memberSince",
        )
        read_only_fields = ("email", "memberSince")


class FollowSerializer(serializers.ModelSerializer):
    followerUsername = serializers.CharField(source="follower.username", read_only=True)
    followingUsername = serializers.CharField(source="following.username", read_only=True)
    followedAt = serializers.DateTimeField(source="followed_at", read_only=True)

    class Meta:
        model = UserFollow
        fields = ("id", "followerUsername", "followingUsername", "followedAt")
        read_only_fields = ("id", "followerUsername", "followingUsername", "followedAt")
