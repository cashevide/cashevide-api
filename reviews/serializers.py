from rest_framework import serializers

from .models import Review, ReviewedClient, Tag


class ReviewedClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewedClient
        fields = ["id", "phone_number"]


class ClientLookupSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=100, required=True)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "category", "group"]


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["id", "author", "tags", "ratings", "client"]
        read_only_fields = ["author", "client"]

    def validate_tags(self, tags):
        groups = []
        for tag in tags:
            groups.append(tag.group)

        if len(groups) != len(set(groups)):
            seen = set()
            duplicates = set(x for x in groups if x in seen or seen.add(x))
            raise serializers.ValidationError(
                f"You cannot select conflicting tags from the same category: {', '.join(duplicates)}"
            )

        return tags

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


class ReviewListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = serializers.ReadOnlyField(source="author.username")

    class Meta:
        model = Review
        fields = ["id", "tags", "ratings", "author"]


class UserReviewListSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source="author.username")
    tags = TagSerializer(many=True)
    client = ReviewedClientSerializer()

    class Meta:
        model = Review
        fields = ["id", "author", "tags", "client"]
