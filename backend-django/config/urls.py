from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("library.urls")),
    path("api/auth/", include("users.urls.auth")),
    path("api/users/", include("users.urls.users")),
    path("api/u/", include("users.urls.public")),
    path("api/", include("books.urls")),
    path("api/", include("ratings.urls")),
    path("api/shelf/", include("shelf.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
