from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers

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
    dashboard_analytics=extend_schema(
        tags=["Invoices"],
        summary="Get freelancer dashboard analytics",
        description="Fetch user's revenue and outstanding balance analytics grouped by currency across various timeframes.",
        responses={
            200: inline_serializer(
                name="DashboardAnalyticsResponse",
                fields={
                    "revenue": inline_serializer(
                        name="DashboardRevenueSchema",
                        fields={
                            "total": serializers.DictField(
                                child=serializers.FloatField()
                            ),
                            "this_month": serializers.DictField(
                                child=serializers.FloatField()
                            ),
                            "last_month": serializers.DictField(
                                child=serializers.FloatField()
                            ),
                            "last_three_months": serializers.DictField(
                                child=serializers.FloatField()
                            ),
                            "this_year": serializers.DictField(
                                child=serializers.FloatField()
                            ),
                            "last_year": serializers.DictField(
                                child=serializers.FloatField()
                            ),
                        },
                    ),
                    "balance_due": inline_serializer(
                        name="DashboardBalanceDueSchema",
                        fields={
                            "total": serializers.DictField(
                                child=serializers.FloatField()
                            ),
                        },
                    ),
                },
            )
        },
        examples=[
            OpenApiExample(
                name="Dashboard Analytics Success",
                summary="Successful dashboard analytics response with currency breakdown",
                value={
                    "revenue": {
                        "total": {"INR": 400.0, "YEN": 6110.0},
                        "this_month": {"YEN": 2500.0},
                        "last_month": {"INR": 400.0, "YEN": 3400.0},
                        "last_three_months": {"INR": 400.0, "YEN": 3600.0},
                        "this_year": {"INR": 400.0, "YEN": 6100.0},
                        "last_year": {"YEN": 10.0},
                    },
                    "balance_due": {"total": {"YEN": 590.0, "INR": 3100.0}},
                },
                response_only=True,
                status_codes=["200"],
            )
        ],
    ),
)
