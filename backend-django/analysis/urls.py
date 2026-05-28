from django.urls import path

from .views import (
    AIExtractionRetrieveView,
    AIExtractionTriggerView,
    BookCharacterHideView,
    BookCharacterMergeView,
)

urlpatterns = [
    path("books/<int:book_id>/ai/extract/", AIExtractionTriggerView.as_view()),
    path("books/<int:book_id>/ai/extraction/", AIExtractionRetrieveView.as_view()),
    path(
        "books/<int:book_id>/characters/<int:character_id>/hide/",
        BookCharacterHideView.as_view(),
    ),
    path(
        "books/<int:book_id>/characters/<int:character_id>/merge/",
        BookCharacterMergeView.as_view(),
    ),
]
