from django.urls import path, re_path

from wiki.views import PageDetailView, PageListCreateView, PageVersionListView

# Path without the leading '/': 'books/solaris.md'
PAGE_PATH = r"(?P<path>(?:books|characters|places|universes)/[a-z0-9-]+\.md)"

urlpatterns = [
    path("pages/", PageListCreateView.as_view(), name="wiki-pages"),
    re_path(rf"^pages/{PAGE_PATH}$", PageDetailView.as_view(), name="wiki-page"),
    re_path(
        rf"^pages/{PAGE_PATH}/versions/$",
        PageVersionListView.as_view(),
        name="wiki-page-versions",
    ),
]
