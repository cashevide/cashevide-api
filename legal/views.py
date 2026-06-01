from django.shortcuts import get_object_or_404
from rest_framework.generics import RetrieveAPIView

from .models import LegalDocument
from .schema import LEGAL_VIEW_SCHEMA
from .serializers import LegalDocumentSerializer


@LEGAL_VIEW_SCHEMA
class LatestLegalDocumentView(RetrieveAPIView):
    serializer_class = LegalDocumentSerializer
    permission_classes = []

    def get_object(self):
        doc_type = self.kwargs.get("doc_type")

        doc_mapping = {
            "privacy": "PRIVACY",
            "privacy-policy": "PRIVACY",
            "terms": "TERMS",
            "terms-and-conditions": "TERMS",
        }

        db_doc_type = doc_mapping.get(doc_type.lower(), doc_type.upper())

        return get_object_or_404(
            LegalDocument, document_type=db_doc_type, is_active=True
        )
