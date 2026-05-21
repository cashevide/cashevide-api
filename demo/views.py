from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet

from demo.models import Invoice
from demo.serializers import InvoiceSerializer


class InvoiceViewSet(ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [AllowAny]
    pagination_class = None
