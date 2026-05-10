from django.urls import path
from library.views import AuthorListCreateView, AuthorRetrieveUpdateDestroyView

urlpatterns = [
    path("", AuthorListCreateView.as_view()),
    path("<int:pk>/", AuthorRetrieveUpdateDestroyView.as_view()),
]
