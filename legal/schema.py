from drf_spectacular.utils import extend_schema, extend_schema_view

LEGAL_VIEW_SCHEMA = extend_schema_view(
    get=extend_schema(
        tags=["Legal"],
        summary="Get latest active legal document",
        description="Fetch the currently active version of a legal document (e.g., 'terms' or 'privacy-policy') based on the type provided in the URL.",
    ),
)
