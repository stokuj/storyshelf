from django.urls import path

from library.views import AuthorListView, AuthorRetrieveView

urlpatterns = [
    path("", AuthorListView.as_view()),
    path("<int:pk>/", AuthorRetrieveView.as_view()),
]
