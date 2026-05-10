# Django Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Spring Boot backend with Django + DRF, swap Kafka for RabbitMQ + Celery, keep the same Vue 3 frontend and FastAPI NLP microservice.

**Architecture:** 6 Django apps (`users`, `books`, `reviews`, `shelf`, `library`, `analysis`) in a new `backend-django/` folder alongside existing `backend/`. Celery workers call NLP via HTTP. NLP calls back to Django via `/api/internal/*` endpoints. Frontend switches from session cookies to JWT. Django Admin replaces Vue admin views.

**Tech Stack:** Django 5.x, DRF, simplejwt, Celery, RabbitMQ, PostgreSQL, Gunicorn `-w 4`

---

## File Map

### Created (`backend-django/`)

```
backend-django/
├── manage.py, requirements.txt, Dockerfile
├── config/
│   ├── __init__.py, urls.py, wsgi.py, celery.py
│   └── settings/ (__init__.py, base.py, dev.py, prod.py)
├── users/     (models.py, serializers.py, views.py, urls.py, admin.py, apps.py, tests/)
├── books/     (models.py, serializers.py, views.py, urls.py, admin.py, apps.py, tests/)
├── reviews/   (models.py, serializers.py, views.py, urls.py, admin.py, apps.py, tests/)
├── shelf/     (models.py, serializers.py, views.py, urls.py, apps.py, tests/)
├── library/   (models.py, serializers.py, views.py, urls.py, admin.py, apps.py, tests/)
└── analysis/  (tasks.py, callbacks.py, urls.py, middleware.py, apps.py, tests/)
```

### Modified (existing)

| File | Change |
|------|--------|
| `frontend/src/api.js` | +JWT interceptors, -`credentials:'include'` |
| `frontend/src/views/LoginView.vue` | JWT response shape |
| `frontend/src/views/RegisterView.vue` | JWT response shape |
| `frontend/src/router.js` | Remove admin routes |
| `infra/caddy/Caddyfile` | `backend:8080` → `django:8000`, `+ /api/internal/* 403` |
| `infra/compose/docker-compose.dev.yml` | Replace services |
| `infra/compose/docker-compose.prod.yml` | Replace services |
| `.env.example` | New env vars |

### Deleted

```
frontend/src/views/admin/AdminBooksView.vue
frontend/src/views/admin/AdminAuthorsView.vue
frontend/src/views/admin/AdminSeriesView.vue
```

---

### Task 1: Django Project Scaffolding

**Files:**
- Create: `backend-django/manage.py`, `requirements.txt`
- Create: `backend-django/config/__init__.py`, `urls.py`, `wsgi.py`, `celery.py`
- Create: `backend-django/config/settings/__init__.py`, `base.py`, `dev.py`, `prod.py`
- Create: `backend-django/users/__init__.py`, `apps.py`
- Create: `backend-django/books/__init__.py`, `apps.py`
- Create: `backend-django/reviews/__init__.py`, `apps.py`
- Create: `backend-django/shelf/__init__.py`, `apps.py`
- Create: `backend-django/library/__init__.py`, `apps.py`
- Create: `backend-django/analysis/__init__.py`, `apps.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p backend-django/config/settings
mkdir -p backend-django/{users,books,reviews,shelf,library,analysis}/tests
touch backend-django/users/tests/__init__.py
touch backend-django/books/tests/__init__.py
touch backend-django/reviews/tests/__init__.py
touch backend-django/shelf/tests/__init__.py
touch backend-django/library/tests/__init__.py
touch backend-django/analysis/tests/__init__.py
```

- [ ] **Step 2: Create `requirements.txt`**

```txt
django>=6.0,<6.1
djangorestframework>=3.17
djangorestframework-simplejwt>=5.5
django-cors-headers>=4.9
django-filter>=25.2
drf-spectacular>=0.29
celery>=5.6
psycopg2-binary>=2.9
gunicorn>=26.0
requests>=2.33
dj-database-url>=3.1
```

- [ ] **Step 3: Create `config/settings/base.py`**

```python
import os
from datetime import timedelta
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = False
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth",
    "django.contrib.contenttypes", "django.contrib.sessions",
    "django.contrib.messages", "django.contrib.staticfiles",
    "rest_framework", "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders", "django_filters", "drf_spectacular",
    "users.apps.UsersConfig", "books.apps.BooksConfig",
    "reviews.apps.ReviewsConfig", "shelf.apps.ShelfConfig",
    "library.apps.LibraryConfig", "analysis.apps.AnalysisConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "analysis.middleware.InternalEndpointMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [], "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

DATABASES = {"default": dj_database_url.config(
    default="postgres://postgres:secret-key@localhost:5432/booksdb",
    conn_max_age=600,
)}

AUTH_USER_MODEL = "users.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

LANGUAGE_CODE = "en-us"; TIME_ZONE = "UTC"; USE_I18N = True; USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_LIFETIME_MINUTES", "30"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_REFRESH_LIFETIME_MINUTES", "1440"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "amqp://rabbitmq:5672//")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_DEFAULT_RETRY_DELAY = 10
CELERY_TASK_MAX_RETRIES = 3

NLP_SERVICE_URL = os.getenv("NLP_SERVICE_URL", "http://nlp-service:8000")

SPECTACULAR_SETTINGS = {"TITLE": "StoryShelf API", "VERSION": "1.0.0"}
```

- [ ] **Step 4: Create `config/settings/dev.py` and `prod.py`**

```python
# backend-django/config/settings/dev.py
from .base import *  # noqa: F401, F403
DEBUG = True
SECRET_KEY = "dev-not-for-production"
CELERY_TASK_ALWAYS_EAGER = True
CORS_ALLOW_ALL_ORIGINS = True
```

```python
# backend-django/config/settings/prod.py
from .base import *  # noqa: F401, F403
DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
CORS_ALLOWED_ORIGINS = []  # set via env in production
```

```python
# backend-django/config/settings/__init__.py
import os
DJANGO_ENV = os.getenv("DJANGO_ENV", "dev")
if DJANGO_ENV == "prod":
    from .prod import *  # noqa: F401, F403
else:
    from .dev import *  # noqa: F401, F403
```

- [ ] **Step 5: Create `config/urls.py`, `wsgi.py`, `celery.py`, `__init__.py`**

```python
# backend-django/config/urls.py
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("users.urls.auth")),
    path("api/users/", include("users.urls.users")),
    path("api/books/", include("books.urls")),
    path("api/shelf/", include("shelf.urls")),
    path("api/authors/", include("library.urls.authors")),
    path("api/series/", include("library.urls.series")),
    path("api/reviews/", include("reviews.urls")),
    path("api/internal/", include("analysis.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
```

```python
# backend-django/config/wsgi.py
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_wsgi_application()
```

```python
# backend-django/config/celery.py
import os
from celery import Celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
app = Celery("storyshelf")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

```python
# backend-django/config/__init__.py
from .celery import app as celery_app
__all__ = ("celery_app",)
```

```python
# backend-django/manage.py
#!/usr/bin/env python
import os, sys
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
```

- [ ] **Step 6: Create all `apps.py` files**

```python
# backend-django/users/apps.py
from django.apps import AppConfig
class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
```

Repeat for `books` (`BooksConfig`, name `books`), `reviews` (`ReviewsConfig`), `shelf` (`ShelfConfig`), `library` (`LibraryConfig`), `analysis` (`AnalysisConfig`). Each `name` matches the directory name.

- [ ] **Step 7: Verify project boots**

```bash
cd backend-django && python manage.py check
```

Expected: "System check identified no issues (0 silenced)."

- [ ] **Step 8: Commit**

```bash
git add backend-django/
git commit -m "feat: scaffold Django project with 6 apps, Celery, DRF, JWT"
```

---

### Task 2: User Model & Auth

**Files:**
- Create: `backend-django/users/models.py`, `serializers.py`, `views.py`
- Create: `backend-django/users/urls/__init__.py`, `auth.py`, `users.py`
- Create: `backend-django/users/admin.py`

- [ ] **Step 1: Create `users/models.py`**

```python
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra):
        if not email: raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(email, username, password, **extra)

class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        USER = "USER"; MODERATOR = "MODERATOR"; ADMIN = "ADMIN"

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=30, unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)
    bio = models.TextField(max_length=500, blank=True, default="")
    avatar_url = models.URLField(blank=True, default="")
    profile_public = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

class UserFollow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following_set")
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name="follower_set")
    followed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("follower", "following")
```

- [ ] **Step 2: Run initial migration**

```bash
cd backend-django && python manage.py makemigrations users && python manage.py migrate
```

- [ ] **Step 3: Create `users/serializers.py`**

```python
from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import User, UserFollow

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(min_length=6, max_length=72, write_only=True)
    username = serializers.RegexField(r"^[a-z]{3,30}$")

    class Meta:
        model = User
        fields = ("email", "username", "password")

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(request=self.context.get("request"), **attrs)
        if user is None:
            raise serializers.ValidationError("Invalid email or password")
        attrs["user"] = user
        return attrs

class UserProfileSerializer(serializers.ModelSerializer):
    member_since = serializers.DateTimeField(source="created_at", read_only=True)
    class Meta:
        model = User
        fields = ("username", "bio", "avatar_url", "member_since")
        read_only_fields = fields

class UserSettingsSerializer(serializers.ModelSerializer):
    member_since = serializers.DateTimeField(source="created_at", read_only=True)
    class Meta:
        model = User
        fields = ("username", "email", "bio", "avatar_url", "role", "profile_public", "member_since")
        read_only_fields = ("email", "role", "member_since")

class FollowSerializer(serializers.ModelSerializer):
    follower_username = serializers.CharField(source="follower.username", read_only=True)
    following_username = serializers.CharField(source="following.username", read_only=True)
    class Meta:
        model = UserFollow
        fields = ("id", "follower_username", "following_username", "followed_at")
        read_only_fields = fields
```

- [ ] **Step 4: Create `users/views.py`**

```python
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserFollow
from .serializers import (
    RegisterSerializer, LoginSerializer, UserProfileSerializer,
    UserSettingsSerializer, FollowSerializer,
)

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return Response({"access": str(refresh.access_token), "refresh": str(refresh)})

class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass
        return Response({"message": "Logged out successfully"})

class AuthMeView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            return Response({
                "authenticated": True, "email": request.user.email,
                "username": request.user.username, "role": request.user.role,
            })
        return Response({"authenticated": False, "email": None, "username": None, "role": None})

class UserProfileView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserProfileSerializer
    lookup_field = "username"
    queryset = User.objects.filter(profile_public=True)

    def get_object(self):
        user = get_object_or_404(User, username=self.kwargs["username"])
        if not user.profile_public and not (self.request.user.is_authenticated and self.request.user == user):
            from django.http import Http404
            raise Http404
        return user

class UserSettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSettingsSerializer
    def get_object(self):
        return self.request.user

class UserVisibilityView(APIView):
    def patch(self, request):
        user = request.user
        user.profile_public = request.query_params.get("profilePublic", "true").lower() == "true"
        user.save()
        return Response(UserSettingsSerializer(user).data)

class UserFollowView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, username):
        target = get_object_or_404(User, username=username)
        if UserFollow.objects.filter(follower=request.user, following=target).exists():
            return Response({"detail": "Already following"}, status=status.HTTP_409_CONFLICT)
        UserFollow.objects.create(follower=request.user, following=target)
        return Response(status=status.HTTP_201_CREATED)

    def delete(self, request, username):
        target = get_object_or_404(User, username=username)
        follow = get_object_or_404(UserFollow, follower=request.user, following=target)
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class FollowListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FollowSerializer
    follower_view = False

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs["username"])
        if self.follower_view:
            return UserFollow.objects.filter(following=user).select_related("follower")
        return UserFollow.objects.filter(follower=user).select_related("following")
```

- [ ] **Step 5: Create `users/urls/auth.py` and `users/urls/users.py`**

```python
# backend-django/users/urls/__init__.py (empty file)
```

```python
# backend-django/users/urls/auth.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from users.views import RegisterView, LoginView, LogoutView, AuthMeView

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("login/", LoginView.as_view()),
    path("refresh/", TokenRefreshView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("me/", AuthMeView.as_view()),
]
```

```python
# backend-django/users/urls/users.py
from django.urls import path
from users.views import (
    UserProfileView, UserSettingsView, UserVisibilityView,
    UserFollowView, FollowListView,
)

urlpatterns = [
    path("me/", UserSettingsView.as_view()),
    path("me/visibility/", UserVisibilityView.as_view()),
    path("<str:username>/", UserProfileView.as_view()),
    path("<str:username>/follow/", UserFollowView.as_view()),
    path("<str:username>/followers/", FollowListView.as_view(follower_view=True)),
    path("<str:username>/following/", FollowListView.as_view(follower_view=False)),
]
```

- [ ] **Step 6: Create `users/admin.py`**

```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserFollow

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "username", "role", "profile_public", "is_active", "created_at")
    list_filter = ("role", "profile_public", "is_active")
    search_fields = ("email", "username")
    ordering = ("-created_at",)
    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Profile", {"fields": ("bio", "avatar_url", "profile_public")}),
        ("Permissions", {"fields": ("role", "is_active", "is_staff", "is_superuser")}),
    )
    add_fieldsets = ((None, {"fields": ("email", "username", "password1", "password2")}),)

@admin.register(UserFollow)
class UserFollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "following", "followed_at")
    search_fields = ("follower__username", "following__username")
```

- [ ] **Step 7: Test auth endpoints**

```bash
cd backend-django && python manage.py createsuperuser --email admin@example.com --username admin

# Start server and test
python manage.py runserver &
sleep 1

# Register
curl -s -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","username":"testuser","password":"test1234"}'
# Expected: {"access":"...","refresh":"..."}

# Login
curl -s -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test1234"}'
# Expected: {"access":"...","refresh":"..."}

kill %1
```

- [ ] **Step 8: Commit**

```bash
git add backend-django/users/
git commit -m "feat: add User model, JWT auth, follow system"
```

---

### Task 3: All Remaining Models

**Files:**
- Create: `backend-django/library/models.py` (Author, Serie, Tag)
- Create: `backend-django/books/models.py` (Book, Chapter, StoryCharacter, BookCharacter, CharacterRelation, BookAuthor, BookTag)
- Create: `backend-django/reviews/models.py` (Review)
- Create: `backend-django/shelf/models.py` (ShelfEntry)

- [ ] **Step 1: Create `library/models.py`**

```python
from django.db import models

class Author(models.Model):
    name = models.CharField(max_length=255)
    bio = models.TextField(blank=True, default="")
    birth_date = models.DateField(null=True, blank=True)

class Serie(models.Model):  # "Series" clashes with Django test internals
    class Status(models.TextChoices):
        ONGOING = "ONGOING"; COMPLETED = "COMPLETED"
        CANCELLED = "CANCELLED"; HIATUS = "HIATUS"
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name_plural = "series"

class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
```

- [ ] **Step 2: Create `books/models.py`**

```python
from django.db import models

class Book(models.Model):
    serie = models.ForeignKey("library.Serie", on_delete=models.SET_NULL, null=True, blank=True, related_name="books")
    title = models.CharField(max_length=500, blank=True, default="")
    year = models.IntegerField(default=0)
    isbn = models.CharField(max_length=20, blank=True, default="")
    description = models.TextField(blank=True, default="")
    page_count = models.IntegerField(default=0)
    position_in_series = models.IntegerField(null=True, blank=True)
    chapters_count = models.IntegerField(default=0)
    ner_completed_count = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)
    ratings_count = models.IntegerField(default=0)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    authors = models.ManyToManyField("library.Author", through="BookAuthor")
    tags = models.ManyToManyField("library.Tag", through="BookTag")
    genres = models.JSONField(default=list)

class BookAuthor(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    author = models.ForeignKey("library.Author", on_delete=models.CASCADE)
    role = models.CharField(max_length=30, blank=True, null=True)
    class Meta:
        unique_together = ("book", "author")

class BookTag(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    tag = models.ForeignKey("library.Tag", on_delete=models.CASCADE)
    class Meta:
        unique_together = ("book", "tag")

class Chapter(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="chapters")
    chapter_number = models.IntegerField()
    title = models.CharField(max_length=150, blank=True, default="")
    content = models.TextField()
    analysis_completed = models.BooleanField(default=False)
    char_count = models.IntegerField(null=True, blank=True)
    char_count_clean = models.IntegerField(null=True, blank=True)
    word_count = models.IntegerField(null=True, blank=True)
    token_count = models.IntegerField(null=True, blank=True)
    ner_result = models.JSONField(null=True, blank=True)
    class Meta:
        ordering = ("chapter_number",)

class StoryCharacter(models.Model):
    name = models.CharField(max_length=255, unique=True)

class BookCharacter(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    character = models.ForeignKey(StoryCharacter, on_delete=models.CASCADE)
    mention_count = models.IntegerField(default=0)
    role = models.CharField(max_length=50, blank=True, null=True)
    class Meta:
        unique_together = ("book", "character")

class CharacterRelation(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="character_relations")
    source = models.ForeignKey(StoryCharacter, on_delete=models.CASCADE, related_name="relations_as_source")
    target = models.ForeignKey(StoryCharacter, on_delete=models.CASCADE, related_name="relations_as_target")
    relation = models.TextField(null=True, blank=True)
    evidence = models.TextField(null=True, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    class Meta:
        unique_together = ("book", "source", "target")
```

- [ ] **Step 3: Create `reviews/models.py`**

```python
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

class Review(models.Model):
    book = models.ForeignKey("books.Book", on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    content = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ("book", "user")
        ordering = ("-created_at",)
```

- [ ] **Step 4: Create `shelf/models.py`**

```python
from django.conf import settings
from django.db import models

class ShelfEntry(models.Model):
    class Status(models.TextChoices):
        WANT_TO_READ = "WANT_TO_READ"; READING = "READING"; READ = "READ"
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shelf_entries")
    book = models.ForeignKey("books.Book", on_delete=models.CASCADE, related_name="shelf_entries")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.WANT_TO_READ)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ("user", "book")
        ordering = ("-created_at",)
```

- [ ] **Step 5: Run all migrations**

```bash
cd backend-django && python manage.py makemigrations library books reviews shelf && python manage.py migrate
```

- [ ] **Step 6: Commit**

```bash
git add backend-django/library/ backend-django/books/ backend-django/reviews/ backend-django/shelf/
git commit -m "feat: add all remaining models (Library, Books, Reviews, Shelf)"
```

---

### Task 4: DRF Serializers & Views — Library, Reviews, Shelf

**Files:**
- Create: `backend-django/library/serializers.py`, `views.py`, `urls.py` (splits into authors/series), `admin.py`
- Create: `backend-django/reviews/serializers.py`, `views.py`, `urls.py`, `admin.py`
- Create: `backend-django/shelf/serializers.py`, `views.py`, `urls.py`

- [ ] **Step 1: Create `library/serializers.py`**

```python
from rest_framework import serializers
from .models import Author, Serie, Tag

class AuthorSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    class Meta:
        model = Author
        fields = ("id", "name", "bio", "avatar_url", "birth_date")
    def get_avatar_url(self, obj):
        return None  # matches Spring behavior (always null)

class SeriesSerializer(serializers.ModelSerializer):
    cover_url = serializers.SerializerMethodField()
    class Meta:
        model = Serie
        fields = ("id", "name", "description", "cover_url", "status")
    def get_cover_url(self, obj):
        return None
```

- [ ] **Step 2: Create `library/views.py`**

```python
from rest_framework import generics, permissions
from .models import Author, Serie
from .serializers import AuthorSerializer, SeriesSerializer

class IsModeratorOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role in ("MODERATOR", "ADMIN")

class AuthorListCreateView(generics.ListCreateAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsModeratorOrReadOnly]

class AuthorRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsModeratorOrReadOnly]

class SeriesListCreateView(generics.ListCreateAPIView):
    queryset = Serie.objects.all()
    serializer_class = SeriesSerializer
    permission_classes = [IsModeratorOrReadOnly]

class SeriesRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Serie.objects.all()
    serializer_class = SeriesSerializer
    permission_classes = [IsModeratorOrReadOnly]
```

- [ ] **Step 3: Create `library/urls.py` (with sub-path splitting)**

```python
# backend-django/library/urls/__init__.py (empty)
mkdir -p backend-django/library/urls
```

```python
# backend-django/library/urls/authors.py
from django.urls import path
from library.views import AuthorListCreateView, AuthorRetrieveUpdateDestroyView

urlpatterns = [
    path("", AuthorListCreateView.as_view()),
    path("<int:pk>/", AuthorRetrieveUpdateDestroyView.as_view()),
]
```

```python
# backend-django/library/urls/series.py
from django.urls import path
from library.views import SeriesListCreateView, SeriesRetrieveUpdateDestroyView

urlpatterns = [
    path("", SeriesListCreateView.as_view()),
    path("<int:pk>/", SeriesRetrieveUpdateDestroyView.as_view()),
]
```

- [ ] **Step 4: Create `library/admin.py`**

```python
from django.contrib import admin
from .models import Author, Serie, Tag

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name", "birth_date")
    search_fields = ("name",)

@admin.register(Serie)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ("name", "status")

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
```

- [ ] **Step 5: Create `reviews/serializers.py` and `reviews/views.py`**

```python
# backend-django/reviews/serializers.py
from rest_framework import serializers
from .models import Review

class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    book_title = serializers.CharField(source="book.title", read_only=True)
    book_id = serializers.IntegerField(source="book.id", read_only=True)

    class Meta:
        model = Review
        fields = ("id", "username", "rating", "content", "created_at", "book_title", "book_id")
        read_only_fields = ("id", "username", "book_title", "book_id", "created_at")
```

```python
# backend-django/reviews/views.py
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Review
from .serializers import ReviewSerializer

class IsModeratorForDelete(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "DELETE":
            return request.user.is_authenticated and request.user.role in ("MODERATOR", "ADMIN")
        return True

class BookReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(book_id=self.kwargs["book_id"]).select_related("user", "book").order_by("-created_at")

# At top of views.py:
from books.models import Book

class BookReviewListCreateView(generics.ListCreateAPIView):
    ...
    def perform_create(self, serializer):
        book = get_object_or_404(Book, id=self.kwargs["book_id"])
        serializer.save(user=self.request.user, book=book)

class ReviewDeleteView(generics.DestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsModeratorForDelete]
```

- [ ] **Step 6: Create `reviews/urls.py` and `reviews/admin.py`**

Spring URLs: `GET/POST /api/books/{id}/reviews` and `DELETE /api/reviews/{id}`.  
Solution: Book review CRUD goes in `books/urls.py`. Delete-only in `reviews/urls.py`.

```python
# backend-django/reviews/urls.py
from django.urls import path
from .views import ReviewDeleteView

urlpatterns = [
    path("<int:pk>/", ReviewDeleteView.as_view()),
]
```

And in `books/urls.py` (see Task 5 Step 3), add:
```python
from reviews.views import BookReviewListCreateView

urlpatterns = [
    ...
    path("<int:pk>/reviews/", BookReviewListCreateView.as_view()),  # GET + POST /api/books/{id}/reviews/
    ...
]
```

This matches the Spring API exactly:
- `GET/POST /api/books/{id}/reviews/` — handled by `books.urls`
- `DELETE /api/reviews/{id}/` — handled by `reviews.urls` (under `/api/reviews/` prefix)

```python
# backend-django/reviews/admin.py
from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("book", "user", "rating", "content_preview", "created_at")
    list_filter = ("rating",)
    search_fields = ("book__title", "user__username")

    @admin.display(description="Content")
    def content_preview(self, obj):
        return obj.content[:100]
```

- [ ] **Step 7: Create `shelf/serializers.py`, `shelf/views.py`, `shelf/urls.py`**

```python
# backend-django/shelf/serializers.py
from rest_framework import serializers
from .models import ShelfEntry

class ShelfEntrySerializer(serializers.ModelSerializer):
    book = serializers.SerializerMethodField()

    class Meta:
        model = ShelfEntry
        fields = ("book", "status", "created_at")

    def get_book(self, obj):
        return {"id": obj.book.id, "title": obj.book.title, "author": obj.book.authors.first().name if obj.book.authors.exists() else None}
```

```python
# backend-django/shelf/views.py
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import ShelfEntry
from books.models import Book
from .serializers import ShelfEntrySerializer

class ShelfListView(generics.ListCreateAPIView):
    serializer_class = ShelfEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ShelfEntry.objects.filter(user=self.request.user).select_related("book").order_by("-created_at")

    def perform_create(self, request, *args, **kwargs):
        book_id = self.kwargs["book_id"]
        book = get_object_or_404(Book, id=book_id)
        status_val = request.data.get("status", "WANT_TO_READ")
        entry, _ = ShelfEntry.objects.get_or_create(
            user=request.user, book=book, defaults={"status": status_val}
        )
        return entry  # handled in post() override below

    def create(self, request, *args, **kwargs):
        entry = self.perform_create(request, *args, **kwargs)
        return Response(self.get_serializer(entry).data, status=status.HTTP_201_CREATED)

class ShelfEntryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ShelfEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return get_object_or_404(ShelfEntry, user=self.request.user, book_id=self.kwargs["book_id"])
```

```python
# backend-django/shelf/urls.py
from django.urls import path
from .views import ShelfListView, ShelfEntryDetailView

urlpatterns = [
    path("", ShelfListView.as_view()),  # GET /api/shelf/
    path("<int:book_id>/", ShelfEntryDetailView.as_view()),  # GET/PATCH/DELETE /api/shelf/{book_id}/
]
```

Wait — `ShelfListView` needs `book_id` for POST but `urls.py` has it at `shelf/` without book_id. The Spring API has `POST /api/shelf/{bookId}` for adding a book. Let's adjust:

```python
# backend-django/shelf/views.py (corrected)
class ShelfAddView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, book_id=None):
        # POST /api/shelf/ (if book_id in request.data) or POST /api/shelf/{book_id}/
        bid = book_id or request.data.get("bookId") or request.data.get("book_id")
        if not bid:
            return Response({"detail": "book_id required"}, status=400)
        book = get_object_or_404(Book, id=bid)
        status_val = request.data.get("status", "WANT_TO_READ")
        entry, created = ShelfEntry.objects.get_or_create(
            user=request.user, book=book, defaults={"status": status_val}
        )
        if not created:
            return Response(ShelfEntrySerializer(entry).data, status=200)
        return Response(ShelfEntrySerializer(entry).data, status=201)
```

But the frontend `api.js` uses `addToBookshelf(bookId, status)` which calls `POST /api/shelf/{bookId}`. So let's map matching paths:

```python
# backend-django/shelf/urls.py (final)
from django.urls import path
from .views import ShelfListView, ShelfEntryDetailView, ShelfAddView

urlpatterns = [
    path("", ShelfListView.as_view()),             # GET /api/shelf/
    path("<int:book_id>/", ShelfAddView.as_view()), # POST /api/shelf/{book_id}/
]
```

And `ShelfEntryDetailView` need a separate pattern... actually frontend calls:
- `GET /api/shelf/{bookId}` → fetches entry for a specific book
- `PATCH /api/shelf/{bookId}` → updates status
- `DELETE /api/shelf/{bookId}` → removes

Let's combine POST/GET/PATCH/DELETE on `shelf/<int:book_id>/`:

```python
# backend-django/shelf/views.py (combined)
class ShelfEntryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, book_id):
        entry = get_object_or_404(ShelfEntry, user=request.user, book_id=book_id)
        return Response(ShelfEntrySerializer(entry).data)

    def post(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        status_val = request.data.get("status", "WANT_TO_READ")
        entry, _ = ShelfEntry.objects.get_or_create(
            user=request.user, book=book, defaults={"status": status_val}
        )
        return Response(ShelfEntrySerializer(entry).data, status=status.HTTP_201_CREATED)

    def patch(self, request, book_id):
        entry = get_object_or_404(ShelfEntry, user=request.user, book_id=book_id)
        status_val = request.data.get("status")
        if not status_val:
            return Response({"detail": "status required"}, status=400)
        entry.status = status_val
        entry.save()
        return Response(ShelfEntrySerializer(entry).data)

    def delete(self, request, book_id):
        entry = get_object_or_404(ShelfEntry, user=request.user, book_id=book_id)
        entry.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
```

```python
# backend-django/shelf/urls.py (final)
from django.urls import path
from .views import ShelfListView, ShelfEntryView

urlpatterns = [
    path("", ShelfListView.as_view()),
    path("<int:book_id>/", ShelfEntryView.as_view()),
]
```

- [ ] **Step 8: Commit**

```bash
git add backend-django/library/ backend-django/reviews/ backend-django/shelf/
git commit -m "feat: add serializers, views, URLs for Library, Reviews, Shelf"
```

---

### Task 5: Books API (Serializers, Views, URLs, Admin)

**Files:**
- Create: `backend-django/books/serializers.py`, `views.py`, `urls.py`, `admin.py`

- [ ] **Step 1: Create `books/serializers.py`**

```python
from rest_framework import serializers
from .models import Book, Chapter, BookCharacter, CharacterRelation
from library.models import Tag

class ChapterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = ("id", "book_id", "chapter_number", "title", "analysis_completed",
                  "char_count", "char_count_clean", "word_count", "token_count")
        read_only_fields = ("book_id", "analysis_completed")

class BookCharacterSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="character.id")
    name = serializers.CharField(source="character.name")

    class Meta:
        model = BookCharacter
        fields = ("id", "name", "mention_count", "role")

class CharacterRelationSerializer(serializers.ModelSerializer):
    source_character_name = serializers.CharField(source="source.name")
    target_character_name = serializers.CharField(source="target.name")

    class Meta:
        model = CharacterRelation
        fields = ("id", "source_character_name", "target_character_name", "relation", "evidence", "confidence")

class BookSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    genres = serializers.JSONField(default=list)
    tags_display = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = ("id", "title", "author", "year", "isbn", "description",
                  "page_count", "genres", "tags_display", "rating", "ratings_count")

    def get_author(self, obj):
        return obj.authors.first().name if obj.authors.exists() else None

    def get_tags_display(self, obj):
        return [t.name for t in obj.tags.all()]

class BookCreateSerializer(serializers.ModelSerializer):
    author_id = serializers.IntegerField()
    genres = serializers.JSONField(default=list)
    tags = serializers.ListField(child=serializers.CharField(), write_only=True, default=list)

    class Meta:
        model = Book
        fields = ("title", "author_id", "year", "isbn", "description", "page_count", "genres", "tags")

class BookDetailSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    genres = serializers.JSONField(default=list)
    tags_display = serializers.SerializerMethodField()
    analysis_status = serializers.SerializerMethodField()
    chapters = serializers.SerializerMethodField()
    characters = serializers.SerializerMethodField()
    relations = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()
    shelf_entry = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = ("id", "title", "author", "year", "isbn", "description", "page_count",
                  "genres", "tags_display", "rating", "ratings_count",
                  "analysis_status", "chapters", "characters", "relations", "reviews", "shelf_entry")

    def get_author(self, obj): return obj.authors.first().name if obj.authors.exists() else None
    def get_tags_display(self, obj): return [t.name for t in obj.tags.all()]

    def get_analysis_status(self, obj):
        finished = obj.ner_completed_count >= obj.chapters_count if obj.chapters_count > 0 else False
        return {"chapters_count": obj.chapters_count, "ner_completed_count": obj.ner_completed_count, "analysis_finished": finished}

    def get_chapters(self, obj):
        return ChapterSerializer(obj.chapters.order_by("chapter_number"), many=True).data

    def get_characters(self, obj):
        return BookCharacterSerializer(obj.bookcharacter_set.select_related("character"), many=True).data

    def get_relations(self, obj):
        return CharacterRelationSerializer(obj.character_relations.select_related("source", "target"), many=True).data

    def get_reviews(self, obj):
        from reviews.serializers import ReviewSerializer
        return ReviewSerializer(obj.reviews.select_related("user").order_by("-created_at"), many=True).data

    def get_shelf_entry(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            try:
                entry = obj.shelf_entries.get(user=request.user)
                from shelf.serializers import ShelfEntrySerializer
                return ShelfEntrySerializer(entry).data
            except Exception:
                pass
        return None
```

- [ ] **Step 2: Create `books/views.py`**

```python
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView

from .models import Book, Chapter, BookAuthor, BookCharacter, CharacterRelation
from library.models import Author, Tag
from .serializers import (
    BookSerializer, BookCreateSerializer, BookDetailSerializer,
    ChapterSerializer, BookCharacterSerializer, CharacterRelationSerializer,
)

class IsModerator(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ("MODERATOR", "ADMIN")

class BookListCreateView(generics.ListCreateAPIView):
    def get_serializer_class(self):
        return BookCreateSerializer if self.request.method == "POST" else BookSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsModerator()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        qs = Book.objects.select_related("serie").prefetch_related("authors", "tags")
        q = self.request.query_params.get("q", "")
        if q:
            q_lower = q.lower()
            qs = qs.filter(
                Q(title__icontains=q_lower) |
                Q(bookauthor__author__name__icontains=q_lower) |
                Q(genres__icontains=q_lower)
            ).distinct()
        return qs

    def perform_create(self, serializer):
        author_id = serializer.validated_data.pop("author_id")
        tags_list = serializer.validated_data.pop("tags", [])
        book = serializer.save()
        Author.objects.filter(id=author_id).exists() or (_ for _ in ()).throw(  # noqa
            Exception(f"Author {author_id} not found")
        )
        BookAuthor.objects.create(book=book, author_id=author_id)
        for tag_name in tags_list:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            book.tags.add(tag)
```

Fix the author lookup — use a proper validation error:

```python
    def perform_create(self, serializer):
        author_id = serializer.validated_data.pop("author_id")
        tags_list = serializer.validated_data.pop("tags", [])
        author = get_object_or_404(Author, id=author_id)
        book = serializer.save()
        BookAuthor.objects.create(book=book, author=author)
        for tag_name in tags_list:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            book.tags.add(tag)
```

```python
class BookDetailView(generics.RetrieveUpdateDestroyAPIView):

    def get_serializer_class(self):
        return BookDetailSerializer if self.request.method == "GET" else BookSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsModerator()]

    def get_queryset(self):
        return Book.objects.prefetch_related(
            Prefetch("chapters", queryset=Chapter.objects.order_by("chapter_number")),
            Prefetch("bookcharacter_set", queryset=BookCharacter.objects.select_related("character")),
            Prefetch("character_relations", queryset=CharacterRelation.objects.select_related("source", "target")),
            Prefetch("reviews"),
            "authors", "tags",
        )

class ChapterView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsModerator()]

    def get(self, request, book_id):
        chapters = Chapter.objects.filter(book_id=book_id).order_by("chapter_number")
        return Response(ChapterSerializer(chapters, many=True).data)

    def post(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"detail": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        text = uploaded_file.read().decode("utf-8")
        raw_chapters = [c.strip() for c in text.split("\n\n") if c.strip()]
        chapters_created = 0

        for i, content in enumerate(raw_chapters):
            chapter_num = i + 1
            title = content.split("\n")[0][:150] if "\n" in content else content[:150]
            chapter = Chapter.objects.create(
                book=book, chapter_number=chapter_num, title=title, content=content
            )
            from analysis.tasks import analyse_chapter, ner_chapter
            analyse_chapter.delay(chapter.id, content)
            if chapter_num == 1:
                ner_chapter.delay(chapter.id, content)
            chapters_created += 1

        book.chapters_count = chapters_created
        book.save()
        return Response({"bookId": book.id, "chaptersCreated": chapters_created}, status=status.HTTP_201_CREATED)

    def delete(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        book.chapters.all().delete()
        book.chapters_count = 0
        book.ner_completed_count = 0
        book.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

class BookCharactersView(generics.ListAPIView):
    serializer_class = BookCharacterSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return BookCharacter.objects.filter(book_id=self.kwargs["book_id"]).select_related("character")

class BookRelationsView(generics.ListAPIView):
    serializer_class = CharacterRelationSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return CharacterRelation.objects.filter(book_id=self.kwargs["book_id"]).select_related("source", "target")
```

- [ ] **Step 3: Create `books/urls.py`**

```python
from django.urls import path
from .views import BookListCreateView, BookDetailView, ChapterView, BookCharactersView, BookRelationsView
from reviews.views import BookReviewListCreateView

urlpatterns = [
    path("", BookListCreateView.as_view()),
    path("<int:pk>/", BookDetailView.as_view()),
    path("<int:pk>/details/", BookDetailView.as_view()),  # alias for details
    path("<int:pk>/reviews/", BookReviewListCreateView.as_view()),  # GET/POST /api/books/{id}/reviews/
    path("<int:book_id>/chapters/", ChapterView.as_view()),
    path("<int:book_id>/characters/", BookCharactersView.as_view()),
    path("<int:book_id>/relations/", BookRelationsView.as_view()),
]
```

- [ ] **Step 4: Create `books/admin.py`**

```python
from django.contrib import admin
from .models import Book, Chapter, StoryCharacter, BookCharacter, CharacterRelation, BookAuthor, BookTag

class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 0
    fields = ("chapter_number", "title", "analysis_completed")

class BookAuthorInline(admin.TabularInline):
    model = BookAuthor
    extra = 1

class BookCharacterInline(admin.TabularInline):
    model = BookCharacter
    extra = 0

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "year", "rating", "ratings_count", "chapters_count")
    search_fields = ("title", "bookauthor__author__name", "genres")
    inlines = [ChapterInline, BookAuthorInline, BookCharacterInline]

@admin.register(StoryCharacter)
class StoryCharacterAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.register(CharacterRelation)
class CharacterRelationAdmin(admin.ModelAdmin):
    list_display = ("book", "source", "target", "relation", "confidence")
    list_filter = ("book",)
```

- [ ] **Step 5: Commit**

```bash
git add backend-django/books/
git commit -m "feat: add Books API with detail aggregator, chapter upload, admin inlines"
```

---

### Task 6: Celery Pipeline & Analysis Callbacks

**Files:**
- Create: `backend-django/analysis/tasks.py`, `callbacks.py`, `urls.py`, `middleware.py`

- [ ] **Step 1: Create `analysis/middleware.py`**

```python
import ipaddress
from django.http import HttpResponseForbidden

DOCKER_NETWORK = ipaddress.ip_network("172.16.0.0/12")

class InternalEndpointMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/api/internal/"):
            client_ip = ipaddress.ip_address(request.META.get("REMOTE_ADDR", "0.0.0.0"))
            if client_ip not in DOCKER_NETWORK:
                return HttpResponseForbidden("Internal endpoint")
        return self.get_response(request)
```

- [ ] **Step 2: Create `analysis/tasks.py`**

```python
import requests
from celery import shared_task
from django.conf import settings

HTTP_TIMEOUT = 60

@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def analyse_chapter(self, chapter_id: int, content: str):
    try:
        resp = requests.post(
            f"{settings.NLP_SERVICE_URL}/chapters/{chapter_id}/analyse",
            json={"content": content},
            timeout=HTTP_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        self.retry(exc=exc)

@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def ner_chapter(self, chapter_id: int, content: str):
    try:
        resp = requests.post(
            f"{settings.NLP_SERVICE_URL}/chapters/{chapter_id}/ner",
            json={"content": content},
            timeout=HTTP_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        self.retry(exc=exc)

@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def find_pairs(self, book_id: int):
    try:
        from books.models import Book, Chapter, BookCharacter
        book = Book.objects.prefetch_related("chapters", "bookcharacter_set__character").get(id=book_id)
        full_text = " ".join(c.content for c in book.chapters.order_by("chapter_number"))
        characters = {
            bc.character.name: bc.mention_count
            for bc in book.bookcharacter_set.all()
        }
        resp = requests.post(
            f"{settings.NLP_SERVICE_URL}/books/{book_id}/find-pairs",
            json={"content": full_text, "characters": characters},
            timeout=HTTP_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        self.retry(exc=exc)

@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def relations_for_book(self, book_id: int):
    try:
        from books.models import CharacterRelation
        pairs = list(
            CharacterRelation.objects.filter(book_id=book_id, relation__isnull=True)
            .values_list("source__name", "target__name")
        )
        if not pairs:
            return
        resp = requests.post(
            f"{settings.NLP_SERVICE_URL}/books/{book_id}/relations",
            json={"pairs": [[s, t] for s, t in pairs]},
            timeout=HTTP_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        self.retry(exc=exc)
```

- [ ] **Step 3: Create `analysis/callbacks.py`**

```python
from django.db.models import F
from django.db import transaction
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from books.models import Book, Chapter, StoryCharacter, BookCharacter, CharacterRelation
from .tasks import find_pairs, relations_for_book


class AnalyseResultView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, chapter_id):
        chapter = Chapter.objects.select_related("book").get(id=chapter_id)
        if chapter.analysis_completed:
            return Response(status=status.HTTP_200_OK)

        data = request.data
        chapter.char_count = data.get("char_count") or data.get("charCount")
        chapter.char_count_clean = data.get("char_count_clean") or data.get("charCountClean")
        chapter.word_count = data.get("word_count") or data.get("wordCount")
        chapter.token_count = data.get("token_count") or data.get("tokenCount")
        chapter.analysis_completed = True
        chapter.save()
        return Response(status=status.HTTP_200_OK)


class NerResultView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, chapter_id):
        with transaction.atomic():
            chapter = Chapter.objects.select_for_update().select_related("book").get(id=chapter_id)
            if chapter.ner_result is not None:
                return Response(status=status.HTTP_200_OK)

            result = request.data.get("result", {})
            characters = result.get("characters", {})
            chapter.ner_result = {"characters": characters}
            chapter.save()

            # Atomic increment
            Book.objects.filter(id=chapter.book_id).update(
                ner_completed_count=F("ner_completed_count") + 1
            )

            # Create/update StoryCharacter + BookCharacter records
            book = Book.objects.get(id=chapter.book_id)
            for name, count in characters.items():
                sc, _ = StoryCharacter.objects.get_or_create(name=name)
                bc, created = BookCharacter.objects.get_or_create(
                    book=book, character=sc,
                    defaults={"mention_count": count, "role": None}
                )
                if not created:
                    bc.mention_count = F("mention_count") + count
                    bc.save(update_fields=["mention_count"])

            # Trigger find_pairs if all NER done
        book.refresh_from_db()
        if book.ner_completed_count >= book.chapters_count:
            find_pairs.delay(book.id)

        return Response(status=status.HTTP_200_OK)


class FindPairsResultView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, book_id):
        if CharacterRelation.objects.filter(book_id=book_id).exists():
            return Response(status=status.HTTP_200_OK)

        pairs = request.data.get("pairs", [])
        for pair in pairs:
            pair_data = pair.get("pair", [])
            if len(pair_data) >= 2:
                source, _ = StoryCharacter.objects.get_or_create(name=pair_data[0])
                target, _ = StoryCharacter.objects.get_or_create(name=pair_data[1])
                CharacterRelation.objects.get_or_create(
                    book_id=book_id, source=source, target=target,
                )

        relations_for_book.delay(book_id)
        return Response(status=status.HTTP_200_OK)


class RelationsResultView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, book_id):
        all_relations = request.data.get("all_relations", [])
        for result_group in all_relations:
            relations_list = result_group.get("relations", {}).get("relations", [])
            for rel in relations_list:
                source_name = rel.get("source")
                target_name = rel.get("target")
                relation_text = rel.get("relation")
                if not source_name or not target_name:
                    continue

                try:
                    source = StoryCharacter.objects.get(name=source_name)
                    target = StoryCharacter.objects.get(name=target_name)
                    cr = CharacterRelation.objects.filter(
                        book_id=book_id, source=source, target=target
                    ).first()
                    if cr and not cr.relation:
                        cr.relation = relation_text
                        cr.evidence = rel.get("evidence")
                        cr.confidence = rel.get("confidence")
                        cr.save()
                except StoryCharacter.DoesNotExist:
                    pass

        return Response(status=status.HTTP_200_OK)
```

- [ ] **Step 4: Create `analysis/urls.py`**

```python
from django.urls import path
from .callbacks import AnalyseResultView, NerResultView, FindPairsResultView, RelationsResultView

urlpatterns = [
    path("chapters/<int:chapter_id>/analyse-result/", AnalyseResultView.as_view()),
    path("chapters/<int:chapter_id>/ner-result/", NerResultView.as_view()),
    path("books/<int:book_id>/find-pairs-result/", FindPairsResultView.as_view()),
    path("books/<int:book_id>/relations-result/", RelationsResultView.as_view()),
]
```

- [ ] **Step 5: Commit**

```bash
git add backend-django/analysis/
git commit -m "feat: add Celery tasks, analysis callbacks, internal endpoint middleware"
```

---

### Task 7: Dockerfile & Infrastructure

**Files:**
- Create: `backend-django/Dockerfile`
- Modify: `infra/compose/docker-compose.dev.yml`, `docker-compose.prod.yml`
- Modify: `infra/caddy/Caddyfile`
- Modify: `.env.example`

- [ ] **Step 1: Create `backend-django/Dockerfile`**

```dockerfile
FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8000

CMD ["gunicorn", "config.wsgi", "-b", "0.0.0.0:8000", "-w", "4"]
```

- [ ] **Step 2: Update `infra/caddy/Caddyfile`** — change backend upstream and add internal block

```diff
- handle_path /api/* {
-     reverse_proxy backend:8080
- }
+ handle_path /api/internal/* {
+     respond "Forbidden" 403
+ }
+ handle_path /api/* {
+     reverse_proxy django:8000
+ }
```

- [ ] **Step 3: Update `infra/compose/docker-compose.dev.yml`** — replace Spring with Django

Replace the `backend` service block with:

```yaml
  django:
    build: ../backend-django
    container_name: storyshelf-django
    environment:
      DJANGO_ENV: dev
      DJANGO_SECRET_KEY: dev-secret-key
      DATABASE_URL: postgres://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-postgres}@db:5432/${POSTGRES_DB:-booksdb}
      CELERY_BROKER_URL: amqp://rabbitmq:5672//
      CELERY_RESULT_BACKEND: redis://redis:6379/0
      NLP_SERVICE_URL: http://nlp-service:8000
    depends_on:
      db:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
    volumes:
      - ../backend-django:/app
    command: python manage.py runserver 0.0.0.0:8000

  celery-worker:
    build: ../backend-django
    container_name: storyshelf-celery-worker
    environment:
      DJANGO_ENV: dev
      DJANGO_SECRET_KEY: dev-secret-key
      DATABASE_URL: postgres://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-postgres}@db:5432/${POSTGRES_DB:-booksdb}
      CELERY_BROKER_URL: amqp://rabbitmq:5672//
      CELERY_RESULT_BACKEND: redis://redis:6379/0
      NLP_SERVICE_URL: http://nlp-service:8000
    depends_on:
      db:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
    command: celery -A config worker -l info -c 4

  rabbitmq:
    image: rabbitmq:4-management-alpine
    container_name: storyshelf-rabbitmq
    ports:
      - "127.0.0.1:15672:15672"
    healthcheck:
      test: rabbitmq-diagnostics -q ping
      interval: 10s
      timeout: 5s
      retries: 5
```

Remove `kafka` and `zookeeper` service blocks entirely.

- [ ] **Step 4: Repeat for `docker-compose.prod.yml`** — same changes but without volumes, with `DJANGO_ENV=prod` and gunicorn command for django service.

- [ ] **Step 5: Update `.env.example`**

```diff
+ DJANGO_SECRET_KEY=CHANGE_ME
+ DJANGO_ENV=prod
+ CELERY_BROKER_URL=amqp://rabbitmq:5672//
+ CELERY_RESULT_BACKEND=redis://redis:6379/0
+ JWT_ACCESS_LIFETIME_MINUTES=30
+ JWT_REFRESH_LIFETIME_MINUTES=1440
```

Remove Kafka-related env vars (`KAFKA_BOOTSTRAP_SERVERS`, etc.)

- [ ] **Step 6: Commit**

```bash
git add backend-django/Dockerfile infra/caddy/Caddyfile infra/compose/ .env.example
git commit -m "feat: add Dockerfile, update compose with Django+Celery+RabbitMQ"
```

---

### Task 8: Frontend JWT Migration

**Files:**
- Modify: `frontend/src/api.js`
- Modify: `frontend/src/views/LoginView.vue`
- Modify: `frontend/src/views/RegisterView.vue`
- Modify: `frontend/src/router.js`
- Delete: `frontend/src/views/admin/AdminBooksView.vue`, `AdminAuthorsView.vue`, `AdminSeriesView.vue`

- [ ] **Step 1: Update `frontend/src/api.js`** — JWT interceptors

```js
// --- Token management ---
let accessToken = localStorage.getItem('access_token')

export function setTokens(access, refresh) {
  accessToken = access
  localStorage.setItem('access_token', access)
  localStorage.setItem('refresh_token', refresh)
}

export function clearTokens() {
  accessToken = null
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

async function refreshAccessToken() {
  const refresh = localStorage.getItem('refresh_token')
  if (!refresh) throw new Error('no refresh token')
  const res = await fetch('/api/auth/refresh/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  })
  if (!res.ok) throw new Error('refresh failed')
  const data = await res.json()
  setTokens(data.access, data.refresh)
  return data.access
}

// --- Updated request wrapper ---
async function request(method, path, body, isFormData = false) {
  const headers = {}
  if (!isFormData) headers['Content-Type'] = 'application/json'
  if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`

  let res = await fetch(path, {
    method,
    headers,
    body: isFormData ? body : body ? JSON.stringify(body) : undefined,
  })

  if (res.status === 401 && accessToken) {
    try {
      await refreshAccessToken()
      headers['Authorization'] = `Bearer ${accessToken}`
      res = await fetch(path, {
        method,
        headers,
        body: isFormData ? body : body ? JSON.stringify(body) : undefined,
      })
    } catch {
      clearTokens()
      throw new Error('Session expired')
    }
  }

  if (res.status === 204) return null
  const data = await res.json()
  if (!res.ok) {
    const msg = data.detail || data.message || data.error || res.statusText
    throw new Error(msg)
  }
  return data
}

// --- Updated auth functions ---
export async function loginUser(email, password) {
  const data = await request('POST', '/api/auth/login/', { email, password })
  setTokens(data.access, data.refresh)
  return data
}

export async function registerUser(username, email, password) {
  const data = await request('POST', '/api/auth/register/', { username, email, password })
  setTokens(data.access, data.refresh)
  return data
}

export async function logoutUser() {
  try {
    await request('POST', '/api/auth/logout/', { refresh: localStorage.getItem('refresh_token') })
  } finally {
    clearTokens()
  }
}

export async function fetchAuthMe() {
  return request('GET', '/api/auth/me/')
}
```

All other 28 exported functions (`fetchBooks`, `fetchAuthors`, `fetchBookDetails`, etc.) keep their existing signatures. Remove any `credentials: 'include'` that was previously in the `request()` wrapper.

- [ ] **Step 2: Update `LoginView.vue`** and `RegisterView.vue` — no changes needed if the response shape `{access, refresh}` is handled inside `api.js`. Verify: current LoginView calls `loginUser(email, password)` and receives data. The new `loginUser` returns `{access, refresh}` which isn't the same as before. LoginView previously expected `{message, username}`. Let's keep the `message`/`username` part by adding to the login response or just adapt the Vue view to ignore the old `message` field.

Simplest fix — Django login returns `{access, refresh}`. In `api.js` `loginUser`, return just this. In `LoginView.vue`, the `onSubmit` handler currently does:
```js
const data = await loginUser(form.email, form.password)
```

It then checks `data.message` or `data.username`. Change this to just check if `data.access` exists (which means success):

```js
// LoginView.vue — onSubmit handler update
const data = await loginUser(form.email, form.password)
if (data.access) {
  router.push('/')  // or wherever it redirects
}
```

Similarly for `RegisterView.vue`. The specific lines depend on the actual Vue file code. The engineer should read the actual LoginView.vue and RegisterView.vue and adapt the success condition.

- [ ] **Step 3: Update `router.js`** — remove admin routes

Remove the following routes (exact names depend on the actual router):
- `/admin/books` → component: AdminBooksView
- `/admin/authors` → component: AdminAuthorsView
- `/admin/series` → component: AdminSeriesView

- [ ] **Step 4: Delete admin views**

```bash
rm frontend/src/views/admin/AdminBooksView.vue
rm frontend/src/views/admin/AdminAuthorsView.vue
rm frontend/src/views/admin/AdminSeriesView.vue
```

- [ ] **Step 5: Verify frontend builds**

```bash
cd frontend && npm run build
```

Expected: builds without errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/
git commit -m "feat: migrate frontend to JWT auth, remove admin views (→ Django Admin)"
```

---

### Task 9: End-to-End Verification

- [ ] **Step 1: Start full stack**

```bash
docker compose -f infra/compose/docker-compose.dev.yml up -d
```

- [ ] **Step 2: Run migrations and create superuser**

```bash
docker compose -f infra/compose/docker-compose.dev.yml exec django python manage.py migrate
docker compose -f infra/compose/docker-compose.dev.yml exec django python manage.py createsuperuser --email admin@example.com --username admin
```

- [ ] **Step 3: Smoke test API**

```bash
# Register
curl -s -X POST http://localhost/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","username":"testuser","password":"test1234"}'

# Login
curl -s -X POST http://localhost/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test1234"}'

# Auth me (with token)
TOKEN=$(curl -s -X POST http://localhost/api/auth/login/ -H "Content-Type: application/json" -d '{"email":"test@test.com","password":"test1234"}' | jq -r .access)
curl -s http://localhost/api/auth/me/ -H "Authorization: Bearer $TOKEN"

# Books search
curl -s http://localhost/api/books/

# Admin panel
curl -s http://localhost/admin/
```

All expected to return 200.

- [ ] **Step 4: Verify Django Admin is functional** — log in at `http://localhost/admin/` with superuser credentials. Confirm BookAdmin with inlines, AuthorAdmin, SeriesAdmin, ReviewAdmin, UserAdmin all render.

- [ ] **Step 5: Verify Celery worker connects**

```bash
docker compose -f infra/compose/docker-compose.dev.yml logs celery-worker | grep "ready"
# Expected: "celery@... ready."
```

- [ ] **Step 6: Commit**

```bash
git commit -m "feat: Django migration complete — functional verification passes"
```
