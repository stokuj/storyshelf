from django.urls import path
from .views import BookReviewListCreateView, ReviewDeleteView

urlpatterns = [
    path("books/<int:book_id>/reviews/", BookReviewListCreateView.as_view()),
    path("<int:pk>/", ReviewDeleteView.as_view()),
]
