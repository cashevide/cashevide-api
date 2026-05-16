from core.views import BaseViewSet

from .models import Product
from .serializers import PRODUCT_CREATION_LIMITS, ProductSerializer


class ProductViewSet(BaseViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    limits_dict = PRODUCT_CREATION_LIMITS
    item_name = "product"

    filterset_fields = ["title"]

    search_fields = ["title", "unit_price"]

    ordering_fields = ["title", "created_at"]

    ordering = ["-created_at"]
