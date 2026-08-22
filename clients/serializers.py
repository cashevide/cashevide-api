from rest_framework import serializers

from clients.models import Client
from core.utils import check_tier_limit
from users.models import UserSubscription

CLIENT_CREATION_LIMITS: dict[str, int] = {
    UserSubscription.Tier.COMMUNITY: 100,
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
            "is_archived",
            "created_at",
            "updated_at",
            "is_active",
        ]
        read_only_fields = ["user", "slug", "created_at", "updated_at"]

    def validate_is_archived(self, value):

        if value is False and self.instance and self.instance.is_archived:
            user = self.context.get("request").user  # type: ignore
            check_tier_limit(
                user=user,
                model_class=Client,
                limits_dict=CLIENT_CREATION_LIMITS,
                action="unarchive",
                item_name="clients",
            )

        return value

    def create(self, validated_data):
        user = self.context.get("request").user  # type:ignore

        check_tier_limit(
            user=user,
            model_class=Client,
            limits_dict=CLIENT_CREATION_LIMITS,
            action="create",
            item_name="clients",
        )

        return super().create(validated_data)
