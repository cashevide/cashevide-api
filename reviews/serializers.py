import phonenumbers
from rest_framework import serializers

from .models import Review, ReviewedClient, Tag
from .utils import hash_phone_number


class ReviewedClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewedClient
        fields = ["id", "phone_number", "created_at", "updated_at", "is_active"]
        read_only_fields = ["created_at", "updated_at"]

    def validate_phone_number(self, value):
        try:
            hashed_phone_number = hash_phone_number(value)
            queryset = ReviewedClient.objects.filter(phone_number=hashed_phone_number)

            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise serializers.ValidationError(
                    "A reviewed client with this phone number already exists."
                )

            return hashed_phone_number

        except (phonenumbers.NumberParseException, ValueError):
            raise serializers.ValidationError("Invalid phone number format")


class ClientLookupSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=100, required=True)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = [
            "id",
            "name",
            "category",
            "group",
            "created_at",
            "updated_at",
            "is_active",
        ]
        read_only_fields = ["created_at", "updated_at"]


class BaseReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            "id",
            "author",
            "ratings",
            "tags",
            "client",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["author", "client", "created_at", "updated_at"]

    def validate_tags(self, tags):
        groups = []
        for tag in tags:
            groups.append(tag.group)

        if len(groups) != len(set(groups)):
            seen = set()
            duplicates = set(x for x in groups if x in seen or seen.add(x))
            raise serializers.ValidationError(
                "You cannot select conflicting tags from the "
                f"same category: {', '.join(duplicates)}"
            )

        return tags


class ReviewSerializer(BaseReviewSerializer):
    def validate(self, attrs):
        request = self.context["request"]
        view = self.context["view"]

        client_id = view.kwargs["client_id"]

        if request.method == "POST":
            if Review.objects.filter(
                author=request.user, client__id=client_id
            ).exists():
                raise serializers.ValidationError(
                    {"detail": "You have already reviewed this client!"}
                )

        return attrs


class UserReviewSerializer(BaseReviewSerializer):
    pass


class BaseReviewListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = serializers.ReadOnlyField(source="author.username")

    class Meta:
        model = Review
        fields = [
            "id",
            "ratings",
            "tags",
            "author",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ReviewListSerializer(BaseReviewListSerializer):
    pass


class UserReviewListSerializer(BaseReviewListSerializer):
    client = ReviewedClientSerializer()

    class Meta(BaseReviewListSerializer.Meta):
        fields = BaseReviewListSerializer.Meta.fields + ["client"]
