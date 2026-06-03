from django.urls import path

from .views import PublicShelfDetailView, PublicShelfListView

urlpatterns = [
    path("", PublicShelfListView.as_view(), name="public-shelf-list"),
    path("<slug:slug>/", PublicShelfDetailView.as_view(), name="public-shelf-detail"),
]
