from django.db import models
from django.utils.text import slugify
from rest_framework import serializers


def check_creation_limit(user, model_class, limits_dict: dict, item_name: str) -> None:
    current_count = model_class.objects.filter(user=user, is_active=True).count()
    user_tier = user.tier

    if user_tier in limits_dict:
        max_allowed = limits_dict[user_tier]
        if current_count >= max_allowed:
            raise serializers.ValidationError(
                f"You cannot create more than {max_allowed} {item_name} in {user_tier} plan"
            )


def get_usage_metadata(user, queryset, limits_dict: dict, item_name: str) -> dict:
    current_count: int = queryset.count()
    user_tier: str | None = user.tier
    max_allowed = limits_dict.get(user_tier)

    return {
        f"current_{item_name}_count": current_count,
        f"max_allowed_{item_name}": max_allowed,
    }


def generate_unique_slug(model_class: type[models.Model], source_text: str) -> str:
    original_slug: str = slugify(source_text)
    unique_slug: str = original_slug
    extension: int = 1

    while model_class.objects.filter(slug=unique_slug).exists():
        unique_slug = f"{original_slug}-{extension}"
        extension += 1

    return unique_slug
