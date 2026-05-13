from django.urls import path

from .views import ShelfEntryView, ShelfListView

urlpatterns = [
    path("", ShelfListView.as_view()),
    path("<int:book_id>/", ShelfEntryView.as_view()),
]
