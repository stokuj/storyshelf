from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "per_page"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "data": data,
            "page": self.page.number,
            "per_page": self.get_page_size(self.request),
            "total": self.page.paginator.count,
        })

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "required": ["data", "page", "per_page", "total"],
            "properties": {
                "data": schema,
                "page": {"type": "integer", "example": 1},
                "per_page": {"type": "integer", "example": 20},
                "total": {"type": "integer", "example": 100},
            },
        }
