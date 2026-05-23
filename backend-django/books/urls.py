from django.urls import path

from reviews.views import BookReviewListCreateView

from .views import BookContainsCharacterView, BookListView, BookRetrieveView

urlpatterns = [
    path("", BookListView.as_view()),
    # contains-character MUSI byc przed <str:id_or_slug> — Django dopasowuje po kolei
    path("contains-character/", BookContainsCharacterView.as_view()),
    # Legacy int-PK routing (backward compat dla Vue do Phase 2.6)
    path("<int:pk>/", BookRetrieveView.as_view()),
    # idOrSlug routing (nowy kontrakt Svelte)
    path("<str:id_or_slug>/", BookRetrieveView.as_view()),
    path("<str:id_or_slug>/reviews/", BookReviewListCreateView.as_view()),
]
