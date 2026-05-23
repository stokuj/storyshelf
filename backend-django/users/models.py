from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.db.models import F, Q


class UserManager(BaseUserManager):
    def create_user(self, email, handle, password=None, **extra):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, handle=handle, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, handle, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(email, handle, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    handle = models.CharField(max_length=30, unique=True)
    display_name = models.CharField(max_length=80, blank=True, default="")
    bio = models.TextField(max_length=500, blank=True, default="")
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    profile_public = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["handle"]

    def __str__(self):
        return self.handle


class UserFollow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following_set")
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name="follower_set")
    followed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "following"],
                name="unique_follower_following",
            ),
            models.CheckConstraint(
                condition=~Q(follower=F("following")),
                name="userfollow_no_self_follow",
            ),
        ]
        indexes = [
            models.Index(fields=["following"], name="userfollow_following_idx"),
        ]

    def __str__(self):
        return f"{self.follower.handle} → {self.following.handle}"
