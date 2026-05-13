from django.urls import path

from .views import BookListView, BookRetrieveView

urlpatterns = [
    path("", BookListView.as_view()),
    path("<int:pk>/", BookRetrieveView.as_view()),
]
