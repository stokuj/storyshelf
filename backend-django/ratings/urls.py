from django.urls import path

from .views import RatingViewSet

urlpatterns = [
    path(
        "ratings/",
        RatingViewSet.as_view({"get": "list", "put": "update"}),
        name="rating-list",
    ),
    path(
        "ratings/<int:pk>/",
        RatingViewSet.as_view({"get": "retrieve", "delete": "destroy"}),
        name="rating-detail",
    ),
]
