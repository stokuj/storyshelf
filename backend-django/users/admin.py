from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from users.models import User, UserFollow


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("handle", "display_name", "email", "is_staff", "profile_public")
    search_fields = ("handle", "email", "display_name")
    ordering = ("handle",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Profile",
            {"fields": ("handle", "display_name", "bio", "avatar", "profile_public")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "handle", "password1", "password2"),
            },
        ),
    )


@admin.register(UserFollow)
class UserFollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "following", "followed_at")
