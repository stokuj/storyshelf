from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response

from wiki import okf, services
from wiki.models import Page, PageVersion
from wiki.serializers import (
    PageCreateSerializer,
    PageEditSerializer,
    PageListSerializer,
    PageSerializer,
    PageVersionSerializer,
)

INVALID = OpenApiResponse(description="Invalid input or OKF content")
PATH_TAKEN = OpenApiResponse(description="Path taken")
STALE = OpenApiResponse(description="Stale base_version")


def get_own_page(request, path):
    """Other users' Pages are 404, not 403."""
    return get_object_or_404(Page, owner=request.user, path=f"/{path}")


class PageListCreateView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(
        parameters=[OpenApiParameter("type", enum=Page.Type.values)],
        responses=PageListSerializer(many=True),
    )
    def get(self, request):
        pages = Page.objects.filter(owner=request.user)
        if page_type := request.query_params.get("type"):
            pages = pages.filter(type=page_type)
        return Response(PageListSerializer(pages, many=True).data)

    @extend_schema(
        request=PageCreateSerializer,
        responses={201: PageSerializer, 400: INVALID, 409: PATH_TAKEN},
    )
    def post(self, request):
        serializer = PageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        try:
            page = services.create_page(request.user, data.pop("type"), **data)
        except okf.OKFError as e:
            return Response({e.field: [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
        except services.PathTaken as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)
        return Response(PageSerializer(page).data, status=status.HTTP_201_CREATED)


class PageDetailView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(responses=PageSerializer)
    def get(self, request, path):
        return Response(PageSerializer(get_own_page(request, path)).data)

    @extend_schema(
        request=PageEditSerializer,
        responses={200: PageSerializer, 400: INVALID, 409: STALE},
    )
    def put(self, request, path):
        page = get_own_page(request, path)
        serializer = PageEditSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            page = services.edit_page(page, **serializer.validated_data)
        except okf.OKFError as e:
            return Response({e.field: [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
        except services.StaleVersion as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)
        return Response(PageSerializer(page).data)


class PageVersionListView(generics.ListAPIView):
    """Historia, newest first, paginated."""

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PageVersionSerializer

    def get_queryset(self):
        # drf-spectacular calls this without a user while building the schema
        if getattr(self, "swagger_fake_view", False):
            return PageVersion.objects.none()
        return get_own_page(self.request, self.kwargs["path"]).versions.all()
