from rest_framework import serializers

from clients.models import Client
from core.utils import check_creation_limit
from users.models import UserSubscription

CLIENT_CREATION_LIMITS: dict[str, int] = {
    UserSubscription.Tier.COMMUNITY: 10,
    UserSubscription.Tier.INDIVIDUAL: 100,
}


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            "id",
            "user",
            "name",
            "email",
            "phone",
            "address",
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
            model_class=Client,
            limits_dict=CLIENT_CREATION_LIMITS,
            item_name="clients",
        )

        return super().create(validated_data)
