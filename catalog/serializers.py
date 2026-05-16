from rest_framework import serializers

from catalog.models import Product
from users.models import UserSubscription

PRODUCT_CREATION_LIMITS: dict[str, int] = {
    UserSubscription.Tier.COMMUNITY: 10,
    UserSubscription.Tier.INDIVIDUAL: 100,
}


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "user",
            "title",
            "description",
            "unit_price",
            "slug",
            "created_at",
            "updated_at",
            "is_active",
        ]
        read_only_fields = ["user", "slug", "created_at", "updated_at"]
