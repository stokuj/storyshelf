from django.urls import path
from .views import ShelfListView, ShelfEntryView

urlpatterns = [
    path("", ShelfListView.as_view()),
    path("<int:book_id>/", ShelfEntryView.as_view()),
]
