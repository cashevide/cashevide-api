from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view

INVOICE_VIEWSET_SCHEMA = extend_schema_view(
    list=extend_schema(
        tags=["Invoices"],
        summary="List all invoices",
        description="Retrieve a list of all invoices.",
    ),
    retrieve=extend_schema(
        tags=["Invoices"],
        summary="Get invoice details",
        description="Fetch the full details of a specific invoice, including its items and payment records.",
    ),
    create=extend_schema(
        tags=["Invoices"],
        summary="Create a new invoice",
        description="Create a new invoice along with its items and payment records. The invoice is automatically linked to the authenticated user.",
    ),
    update=extend_schema(
        tags=["Invoices"],
        summary="Update an invoice",
        description="Completely update an existing invoice, including modifying, adding, or removing items and payment records.",
    ),
    partial_update=extend_schema(
        tags=["Invoices"],
        summary="Partially update an invoice",
        description="Update specific fields of an existing invoice.",
    ),
    destroy=extend_schema(
        tags=["Invoices"],
        summary="Delete an invoice",
        description="Permanently remove an invoice along with its associated items and payments from the system.",
    ),
    download_pdf=extend_schema(
        tags=["Invoices"],
        summary="Download invoice as PDF",
        description="Generates and returns a professional PDF version of the invoice dynamically without saving it on the server.",
        responses={(200, "application/pdf"): OpenApiTypes.BINARY},
    ),
)
