from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers

PRODUCT_VIEWSET_SCHEMA = extend_schema_view(
    list=extend_schema(
        tags=["Catalog"],
        summary="List my products",
        description="Retrieve a list of all products added by the user in the catalog.",
    ),
    retrieve=extend_schema(
        tags=["Catalog"],
        summary="Get details of a specific product",
        description="Fetch the full details of a specific product from the catalog.",
    ),
    create=extend_schema(
        tags=["Catalog"],
        summary="Add a new product",
        description="Create a new product to be listed in the catalog.",
    ),
    update=extend_schema(
        tags=["Catalog"],
        summary="Update a product",
        description="Completely update an existing product's details.",
    ),
    partial_update=extend_schema(
        tags=["Catalog"],
        summary="Partially update a product",
        description="Update specific fields of an existing product.",
    ),
    destroy=extend_schema(
        tags=["Catalog"],
        summary="Delete a product",
        description="Remove a product from the system (Soft delete marks is_active=False).",
    ),
    usage=extend_schema(
        tags=["Catalog"],
        summary="Get product usage metadata",
        description="Returns the current count of products and the maximum allowed limit based on the user's tier.",
        responses={
            200: inline_serializer(
                name="ProductUsageResponse",
                fields={
                    "current_product_count": serializers.IntegerField(),
                    "max_allowed_product": serializers.IntegerField(allow_null=True),
                },
            )
        },
    ),
)
