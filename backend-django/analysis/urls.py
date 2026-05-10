from django.urls import path
from .callbacks import (
    AnalyseResultView,
    NerResultView,
    FindPairsResultView,
    RelationsResultView,
)

urlpatterns = [
    path("chapters/<int:chapter_id>/analyse-result/", AnalyseResultView.as_view()),
    path("chapters/<int:chapter_id>/ner-result/", NerResultView.as_view()),
    path("books/<int:book_id>/find-pairs-result/", FindPairsResultView.as_view()),
    path("books/<int:book_id>/relations-result/", RelationsResultView.as_view()),
]
