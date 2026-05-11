from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers

CLIENT_VIEWSET_SCHEMA = extend_schema_view(
    list=extend_schema(
        tags=["Clients"],
        summary="List my clients",
        description="Retrieve a list of all clients added by the user for invoice generation.",
    ),
    retrieve=extend_schema(
        tags=["Clients"],
        summary="Get details of a specific client",
        description="Fetch the full details of a specific client profile.",
    ),
    create=extend_schema(
        tags=["Clients"],
        summary="Add a new client",
        description="Create a new client profile to use for professional invoices.",
    ),
    update=extend_schema(
        tags=["Clients"],
        summary="Update a client",
        description="Completely update an existing client's details.",
    ),
    partial_update=extend_schema(
        tags=["Clients"],
        summary="Partially update a client",
        description="Update specific fields of an existing client.",
    ),
    destroy=extend_schema(
        tags=["Clients"],
        summary="Delete a client",
        description="Remove a client from the system (Soft delete marks is_active=False).",
    ),
    usage=extend_schema(
        tags=["Clients"],
        summary="Get client usage metadata",
        description="Returns the current count of clients and the maximum allowed limit based on the user's tier.",
        responses={
            200: inline_serializer(
                name="ClientUsageResponse",
                fields={
                    "current_client_count": serializers.IntegerField(),
                    "max_allowed_client": serializers.IntegerField(allow_null=True),
                },
            )
        },
    ),
)
