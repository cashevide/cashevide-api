import io
from typing import Literal

import requests
from django.core.files.base import ContentFile
from django.db import models
from django.utils.text import slugify
from PIL import Image
from rest_framework import serializers


def get_content_file_from_url(url):
    if not url:
        return None

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()

    except requests.RequestException:
        return None

    return ContentFile(response.content, name="profile.jpg")


def process_image(image_field, format: Literal["jpg", "png"], max_size: int):

    img = Image.open(image_field)

    if format == "jpg":
        if img.mode != "RGB":
            img = img.convert("RGB")

        save_options = {"format": "JPEG", "quality": 85}

    elif format == "png":
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")

        save_options = {"format": "PNG", "optimize": True}

    img.thumbnail((max_size, max_size))

    buffer = io.BytesIO()
    img.save(buffer, **save_options)
    buffer.seek(0)

    file_name = image_field.name.rsplit(".", 1)[0] + f".{format}"
    image_field.save(file_name, ContentFile(buffer.getvalue()), save=False)


def check_tier_limit(
    user, model_class, limits_dict: dict, action: str, item_name: str
) -> None:
    current_count = model_class.objects.filter(
        user=user, is_active=True, is_archived=False
    ).count()
    user_tier = user.tier

    if user_tier in limits_dict:
        max_allowed = limits_dict[user_tier]
        if current_count >= max_allowed:
            raise serializers.ValidationError(
                f"You cannot {action} more than {max_allowed} {item_name}"
                f" in {user_tier} plan"
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
