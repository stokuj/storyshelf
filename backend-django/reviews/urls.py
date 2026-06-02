from django.urls import path

from .views import ReviewViewSet

urlpatterns = [
    path(
        "reviews/",
        ReviewViewSet.as_view({"get": "list", "put": "update"}),
        name="review-list",
    ),
    path(
        "reviews/me/",
        ReviewViewSet.as_view({"get": "me"}),
        name="review-me",
    ),
    path(
        "reviews/<int:pk>/",
        ReviewViewSet.as_view({"get": "retrieve", "delete": "destroy"}),
        name="review-detail",
    ),
]
