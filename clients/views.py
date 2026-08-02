from core.views import BaseResourceViewSet

from .models import Client
from .schema import CLIENT_VIEWSET_SCHEMA
from .serializers import CLIENT_CREATION_LIMITS, ClientSerializer


@CLIENT_VIEWSET_SCHEMA
class ClientViewSet(BaseResourceViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    limits_dict = CLIENT_CREATION_LIMITS
    item_name = "client"

    filterset_fields = ["email", "phone"]

    search_fields = ["name", "email", "phone"]

    ordering_fields = ["name", "created_at"]

    ordering = ["-created_at"]
