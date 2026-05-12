from django.urls import path
from library.views import GenreListCreateView, GenreRetrieveUpdateDestroyView

urlpatterns = [
    path("", GenreListCreateView.as_view()),
    path("<int:pk>/", GenreRetrieveUpdateDestroyView.as_view()),
]
