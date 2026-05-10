from django.urls import path
from .views import ReviewDeleteView

urlpatterns = [
    path("<int:pk>/", ReviewDeleteView.as_view()),
]
