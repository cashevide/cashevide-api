from rest_framework import serializers

from catalog.models import Product
from core.utils import check_tier_limit
from users.models import UserSubscription

PRODUCT_CREATION_LIMITS: dict[str, int] = {
    UserSubscription.Tier.COMMUNITY: 2,
    UserSubscription.Tier.INDIVIDUAL: 100,
}


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "user",
            "title",
            "description",
            "unit_price",
            "slug",
            "is_archived",
            "created_at",
            "updated_at",
            "is_active",
        ]
        read_only_fields = ["id", "user", "slug", "created_at", "updated_at"]

    def validate_is_archived(self, value):

        if value is False and self.instance and self.instance.is_archived:
            user = self.context.get("request").user  # type: ignore
            check_tier_limit(
                user=user,
                model_class=Product,
                limits_dict=PRODUCT_CREATION_LIMITS,
                action="unarchive",
                item_name="products",
            )

        return value

    def create(self, validated_data):
        user = self.context.get("request").user  # type:ignore

        check_tier_limit(
            user=user,
            model_class=Product,
            limits_dict=PRODUCT_CREATION_LIMITS,
            action="create",
            item_name="products",
        )

        return super().create(validated_data)
