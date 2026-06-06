from django.urls import path

from .views import CharacterDetailView, CharacterListView, GenerateCharactersView

urlpatterns = [
    path(
        "books/<slug:slug>/characters/generate/",
        GenerateCharactersView.as_view(),
        name="character-generate",
    ),
    path(
        "books/<slug:slug>/characters/",
        CharacterListView.as_view(),
        name="character-list",
    ),
    path(
        "books/<slug:slug>/characters/<slug:char_slug>/",
        CharacterDetailView.as_view(),
        name="character-detail",
    ),
]
