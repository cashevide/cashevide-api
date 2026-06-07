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
