from django.urls import path
from library.views import GenreListView, GenreRetrieveView

urlpatterns = [
    path("", GenreListView.as_view()),
    path("<int:pk>/", GenreRetrieveView.as_view()),
]
