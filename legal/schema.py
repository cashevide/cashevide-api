from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import serializers

from .serializers import LegalDocumentAcceptanceSerializer

LEGAL_VIEW_SCHEMA = extend_schema_view(
    get=extend_schema(
        tags=["Legal"],
        summary="Get latest active legal document",
        description="Fetch the currently active version of a legal document (e.g., 'terms' or 'privacy-policy') based on the type provided in the URL.",
    ),
)


class LegalAcceptanceSuccessSerializer(serializers.Serializer):
    detail = serializers.CharField(
        default="All pending legal documents have been accepted successfully."
    )


ACCEPT_LEGAL_DOCS_VIEW_SCHEMA = extend_schema_view(
    post=extend_schema(
        tags=["Legal"],
        summary="Accept pending legal documents",
        description=(
            "Allows an authenticated user to accept one or more active legal documents "
            "(like Terms and Conditions, Privacy Policy) by passing their IDs in a list."
        ),
        request=LegalDocumentAcceptanceSerializer,
        responses={
            201: OpenApiResponse(
                response=LegalAcceptanceSuccessSerializer,
                description="All pending legal documents have been accepted successfully.",
            ),
            400: OpenApiResponse(
                description="Bad Request. Returned when the payload is invalid or empty."
            ),
        },
    )
)
