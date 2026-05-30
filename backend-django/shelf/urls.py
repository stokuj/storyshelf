from rest_framework.routers import DefaultRouter

from .views import ShelfEntryViewSet

router = DefaultRouter()
router.register(r"entries", ShelfEntryViewSet, basename="shelfentry")
urlpatterns = router.urls
