from rest_framework.routers import DefaultRouter

from .views import AuthorViewSet, GenreViewSet, SerieViewSet, TagViewSet

router = DefaultRouter()
router.register(r"authors", AuthorViewSet, basename="author")
router.register(r"series", SerieViewSet, basename="serie")
router.register(r"genres", GenreViewSet, basename="genre")
router.register(r"tags", TagViewSet, basename="tag")

urlpatterns = router.urls
