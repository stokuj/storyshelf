from django.test import RequestFactory, TestCase
from rest_framework.request import Request

from config.pagination import StandardPagination


class StandardPaginationTest(TestCase):
    def test_paginated_response_shape(self):
        """Response ma klucze data/page/per_page/total."""
        factory = RequestFactory()
        raw_request = factory.get("/", {"page": 1, "per_page": 3})
        request = Request(raw_request)

        paginator = StandardPagination()
        items = list(range(10))
        result = paginator.paginate_queryset(items, request)
        response = paginator.get_paginated_response(result)

        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["per_page"], 3)
        self.assertEqual(response.data["total"], 10)
        self.assertIn("data", response.data)
        self.assertEqual(len(response.data["data"]), 3)

    def test_default_page_size_is_20(self):
        paginator = StandardPagination()
        self.assertEqual(paginator.page_size, 20)

    def test_max_page_size_is_100(self):
        paginator = StandardPagination()
        self.assertEqual(paginator.max_page_size, 100)
