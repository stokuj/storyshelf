from django.urls import path
from .views import (
    BookListView,
    BookRetrieveView,
    ChapterView,
    BookCharactersView,
    BookRelationsView,
)
from reviews.views import BookReviewListCreateView

urlpatterns = [
    path("", BookListView.as_view()),
    path("<int:pk>/", BookRetrieveView.as_view()),
    path("<int:pk>/reviews/", BookReviewListCreateView.as_view()),
    path("<int:book_id>/chapters/", ChapterView.as_view()),
    path("<int:book_id>/characters/", BookCharactersView.as_view()),
    path("<int:book_id>/relations/", BookRelationsView.as_view()),
]
