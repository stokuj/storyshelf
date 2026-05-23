from django.urls import path

from .views import (
    MyShelfBookView,
    MyShelfDetailView,
    MyShelvesView,
    ShelfEntryView,
    ShelfListView,
)

urlpatterns = [
    # Existing — status czytania (nie ruszać):
    path("", ShelfListView.as_view()),
    path("<int:book_id>/", ShelfEntryView.as_view()),
    # New — kolekcje (Phase 2.3):
    path("me/collections/", MyShelvesView.as_view()),
    path("me/collections/<slug:shelf_slug>/", MyShelfDetailView.as_view()),
    path("me/collections/<slug:shelf_slug>/books/<int:book_id>/", MyShelfBookView.as_view()),
]
