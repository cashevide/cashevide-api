from rest_framework import serializers

from .models import LegalDocument


class LegalDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalDocument
        fields = [
            "id",
            "document_type",
            "version",
            "content",
            "effective_date",
            "updated_at",
        ]


class LegalDocumentAcceptanceSerializer(serializers.Serializer):
    legal_doc_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=False
    )

    def validate_legal_doc_ids(self, value):

        unique_ids = set(value)

        existing_ids = set(
            LegalDocument.objects.filter(id__in=unique_ids, is_active=True).values_list(
                "id", flat=True
            )
        )

        invalid_ids = list(unique_ids - existing_ids)

        if invalid_ids:
            raise serializers.ValidationError(
                "The following legal document IDs are "
                f"invalid or inactive: {invalid_ids}"
            )

        return value
