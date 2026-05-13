from django.urls import path

from .views import ReviewDetailView, ReviewListCreateView

urlpatterns = [
    path("", ReviewListCreateView.as_view()),
    path("<int:pk>/", ReviewDetailView.as_view()),
]
