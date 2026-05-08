from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.utils import get_usage_metadata

from .models import Client
from .serializers import CLIENT_CREATION_LIMITS, ClientSerializer


class ClientViewSet(ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    filterset_fields = ["email", "phone"]

    search_fields = ["name", "email", "phone"]

    ordering_fields = ["name", "created_at"]

    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = Client.objects.filter(user=self.request.user)
        if self.action in ["list", "usage"]:
            return queryset.filter(is_active=True)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"])
    def usage(self, request):

        metadata = get_usage_metadata(
            user=self.request.user,
            queryset=self.get_queryset(),
            limits_dict=CLIENT_CREATION_LIMITS,
            item_name="clients",
        )

        return Response(metadata)

    def perform_destroy(self, instance) -> None:
        instance.is_active = False
        instance.save()
