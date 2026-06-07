from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from legal.models import UserLegalDocumentAcceptance

from .models import LegalDocument
from .schema import ACCEPT_LEGAL_DOCS_VIEW_SCHEMA, LEGAL_VIEW_SCHEMA
from .serializers import LegalDocumentAcceptanceSerializer, LegalDocumentSerializer


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


@ACCEPT_LEGAL_DOCS_VIEW_SCHEMA
class AcceptLegalDocumentsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LegalDocumentAcceptanceSerializer(data=request.data)

        if serializer.is_valid():
            legal_doc_ids = serializer.validated_data.get("legal_doc_ids")

            acceptance = [
                UserLegalDocumentAcceptance(
                    user=request.user, legal_document_id=legal_doc_id
                )
                for legal_doc_id in legal_doc_ids
            ]

            UserLegalDocumentAcceptance.objects.bulk_create(
                acceptance, ignore_conflicts=True
            )

            return Response(
                {
                    "detail": (
                        "All pending legal documents have been accepted successfully."
                    )
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
