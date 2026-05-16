from rest_framework import serializers

from catalog.models import Product
from core.utils import check_creation_limit
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

    def create(self, validated_data):
        user = self.context.get("request").user  # type:ignore

        check_creation_limit(
            user=user,
            model_class=Product,
            limits_dict=PRODUCT_CREATION_LIMITS,
            item_name="products",
        )

        return super().create(validated_data)
