from django.core.exceptions import ImproperlyConfigured
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.utils import get_usage_metadata


class BaseResourceViewSet(ModelViewSet):
    queryset = None
    serializer_class = None
    limits_dict: dict = {}
    item_name: str = ""

    lookup_field = "slug"
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    filterset_fields = []

    search_fields = []

    ordering_fields = []

    ordering = []

    actions_to_filter = [
        "list",
        "retrieve",
        "update",
        "partial_update",
        "destroy",
        "usage",
    ]

    def get_queryset(self):
        if self.queryset is None:
            raise ImproperlyConfigured(
                "BaseResourceViewSet needs a queryset. Define it in your child viewset."
            )

        queryset = self.queryset.filter(user=self.request.user)

        if self.action in self.actions_to_filter:
            queryset = queryset.filter(is_active=True)

        if self.action == "usage":
            return queryset.filter(is_archived=False)

        if self.action == "list":
            is_archived_param = self.request.query_params.get("is_archived")
            if is_archived_param and is_archived_param.lower() == "true":
                return queryset.filter(is_archived=True)

            return queryset.filter(is_archived=False)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"])
    def usage(self, request):

        metadata = get_usage_metadata(
            user=self.request.user,
            queryset=self.get_queryset(),
            limits_dict=self.limits_dict,
            item_name=self.item_name,
        )

        return Response(metadata)

    def perform_destroy(self, instance) -> None:
        instance.is_active = False
        instance.save()
