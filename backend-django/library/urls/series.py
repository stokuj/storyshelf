from django.urls import path
from library.views import SeriesListCreateView, SeriesRetrieveUpdateDestroyView

urlpatterns = [
    path("", SeriesListCreateView.as_view()),
    path("<int:pk>/", SeriesRetrieveUpdateDestroyView.as_view()),
]
