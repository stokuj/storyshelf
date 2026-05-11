from django.urls import path
from .views import (
    BookListCreateView,
    BookDetailView,
    ChapterView,
    BookCharactersView,
    BookRelationsView,
)
from reviews.views import BookReviewListCreateView

urlpatterns = [
    path("", BookListCreateView.as_view()),
    path("<int:pk>/", BookDetailView.as_view()),
    path("<int:pk>/reviews/", BookReviewListCreateView.as_view()),
    path("<int:book_id>/chapters/", ChapterView.as_view()),
    path("<int:book_id>/characters/", BookCharactersView.as_view()),
    path("<int:book_id>/relations/", BookRelationsView.as_view()),
]
