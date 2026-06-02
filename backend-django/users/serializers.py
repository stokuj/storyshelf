from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from users.models import User, UserFollow


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(min_length=6, max_length=72, write_only=True)
    handle = serializers.RegexField(
        regex=r"^[a-z]{3,30}$",
        max_length=30,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    display_name = serializers.CharField(
        max_length=80, required=False, default="", allow_blank=True
    )

    class Meta:
        model = User
        fields = ("email", "handle", "display_name", "password")

    def validate_email(self, value):
        return value.lower().strip()

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


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


class UserMePatchSerializer(serializers.ModelSerializer):
    handle = serializers.RegexField(
        regex=r"^[a-z]{3,30}$",
        max_length=30,
        required=False,
    )
    display_name = serializers.CharField(max_length=80, required=False, allow_blank=True)
    bio = serializers.CharField(max_length=500, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ("handle", "display_name", "bio")

    def validate_handle(self, value):
        if User.objects.exclude(pk=self.instance.pk).filter(handle=value).exists():
            raise serializers.ValidationError("This handle is already taken.")
        return value

    def validate_display_name(self, value):
        return value.strip()


class UserMeSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    member_since = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "handle",
            "display_name",
            "email",
            "bio",
            "avatar_url",
            "member_since",
            "profile_public",
        )

    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.avatar.url) if request else obj.avatar.url
        return None


class UserProfileSerializer(serializers.ModelSerializer):
    member_since = serializers.DateTimeField(source="created_at", read_only=True)
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "handle",
            "display_name",
            "bio",
            "avatar_url",
            "member_since",
            "profile_public",
        )

    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.avatar.url) if request else obj.avatar.url
        return None


class UserSettingsPatchSerializer(serializers.Serializer):
    profile_public = serializers.BooleanField(required=False)


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(min_length=6, max_length=72, write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class EmailChangeSerializer(serializers.Serializer):
    new_email = serializers.EmailField()
    current_password = serializers.CharField(write_only=True)

    def validate_new_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value


class AvatarUploadSerializer(serializers.Serializer):
    avatar = serializers.ImageField()

    def validate_avatar(self, file):
        if file.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("Avatar must be under 2 MB.")
        allowed = {"image/jpeg", "image/png", "image/webp"}
        if file.content_type not in allowed:
            raise serializers.ValidationError("Only JPEG, PNG and WebP are allowed.")
        from PIL import Image

        img = Image.open(file)
        img.verify()
        file.seek(0)
        img = Image.open(file)
        if img.width > 1024 or img.height > 1024:
            raise serializers.ValidationError("Dimensions must not exceed 1024×1024 px.")
        file.seek(0)
        return file


class AccountDeleteSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)


class FollowSerializer(serializers.ModelSerializer):
    follower_handle = serializers.CharField(source="follower.handle", read_only=True)
    following_handle = serializers.CharField(source="following.handle", read_only=True)
    followed_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = UserFollow
        fields = ("id", "follower_handle", "following_handle", "followed_at")
