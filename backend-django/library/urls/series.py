from django.urls import path
from library.views import SeriesListView, SeriesRetrieveView

urlpatterns = [
    path("", SeriesListView.as_view()),
    path("<int:pk>/", SeriesRetrieveView.as_view()),
]
