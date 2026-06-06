from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from reviews.views import UserReviewListView
from shelf.views import PublicShelfEntryListView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("library.urls")),
    path("api/auth/", include("users.urls.auth")),
    path("api/users/", include("users.urls.users")),
    path("api/u/", include("users.urls.public")),
    path("api/u/<str:handle>/shelf/", PublicShelfEntryListView.as_view()),
    path("api/u/<str:handle>/reviews/", UserReviewListView.as_view()),
    path("api/u/<str:handle>/shelves/", include("shelf.urls_public")),
    path("api/", include("books.urls")),
    path("api/", include("characters.urls")),
    path("api/", include("ratings.urls")),
    path("api/shelf/", include("shelf.urls")),
    path("api/", include("reviews.urls")),
    path("api/", include("shelf.urls_shelves")),
    path("api/", include("feed.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
