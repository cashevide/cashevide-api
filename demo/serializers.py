from rest_framework import serializers

from demo.models import Book


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            "id",
            "name",
            "price",
            "slug",
            "created_at",
            "updated_at",
            "is_active",
        ]

        read_only_fields = ["slug", "created_at", "updated_at"]
