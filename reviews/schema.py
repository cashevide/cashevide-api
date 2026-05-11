from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers

from .serializers import ClientLookupSerializer

TAG_VIEWSET_SCHEMA = extend_schema_view(
    list=extend_schema(
        tags=["Tags"],
        summary="List all available tags",
        description="Fetch all pre-defined tags that users can select while writing a review.",
    ),
    retrieve=extend_schema(tags=["Tags"], summary="Get details of a specific tag"),
    create=extend_schema(
        tags=["Tags"],
        summary="Create a new pre-defined tag",
        description="Only accessible by superusers. Use this to add tags that users will see in the frontend.",
    ),
    update=extend_schema(tags=["Tags"], summary="Update an existing tag"),
    partial_update=extend_schema(tags=["Tags"], summary="Partially update a tag"),
    destroy=extend_schema(tags=["Tags"], summary="Remove a tag from the system"),
)

CLIENT_VIEWSET_SCHEMA = extend_schema_view(
    list=extend_schema(
        tags=["Reviewed Clients"],
        summary="List all clients (Superuser only)",
        description="Only accessible by superusers to see the full list of clients.",
    ),
    retrieve=extend_schema(
        tags=["Reviewed Clients"],
        summary="Get client details",
        description="Fetch specific details of a client by their ID. Accessible by any authenticated user.",
    ),
    create=extend_schema(
        tags=["Reviewed Clients"],
        summary="Create a new client",
        description="Allow users to add a new client (business) if it's not already in the system before they write a review.",
    ),
    update=extend_schema(
        tags=["Reviewed Clients"], summary="Update client details (Superuser only)"
    ),
    partial_update=extend_schema(
        tags=["Reviewed Clients"],
        summary="Partially update client details (Superuser only)",
    ),
    destroy=extend_schema(
        tags=["Reviewed Clients"], summary="Delete a client (Superuser only)"
    ),
)

CLIENT_LOOKUP_SCHEMA = extend_schema_view(
    post=extend_schema(
        tags=["Reviewed Clients"],
        summary="Lookup Client ID by Phone Number",
        description="Search for a client's unique ID using their phone number. This ID is required to post a review for that specific client.",
        request=ClientLookupSerializer,
        responses={
            200: inline_serializer(
                name="LookupSuccessResponse",
                fields={
                    "client_id": serializers.UUIDField(),
                    "message": serializers.CharField(
                        default="Client found successfully"
                    ),
                },
            ),
            404: inline_serializer(
                name="LookupErrorResponse",
                fields={"error": serializers.CharField(default="Client not found")},
            ),
        },
    )
)

REVIEW_VIEWSET_SCHEMA = extend_schema_view(
    list=extend_schema(
        tags=["Reviews"],
        summary="Get reviews for a client",
        description="Retrieve all reviews associated with a specific client.",
    ),
    summary=extend_schema(
        tags=["Reviews"],
        summary="Get client review summary",
        description="Returns average rating, total reviews, distribution, and tags summary.",
    ),
    create=extend_schema(
        tags=["Reviews"],
        summary="Post a review for a client",
        description="Submit a new review for a specific client.",
    ),
    retrieve=extend_schema(
        tags=["Reviews"],
        summary="Get details of a specific review",
        description="Fetch full details of a specific review.",
    ),
    update=extend_schema(
        tags=["Reviews"],
        summary="Update a review (Superuser only)",
        description="Completely update a review's content.",
    ),
    partial_update=extend_schema(
        tags=["Reviews"],
        summary="Partially update a review (Superuser only)",
        description="Update specific fields of a review.",
    ),
    destroy=extend_schema(
        tags=["Reviews"],
        summary="Delete a review (Superuser only)",
        description="Permanently remove a review from the system.",
    ),
)

USER_REVIEW_VIEWSET_SCHEMA = extend_schema_view(
    list=extend_schema(
        tags=["Reviews"],
        summary="List my reviews",
        description="Retrieve a list of all reviews written by the currently authenticated user.",
    ),
    retrieve=extend_schema(
        tags=["Reviews"],
        summary="Get details of my review",
        description="Fetch the full details of a specific review owned by the user.",
    ),
    update=extend_schema(
        tags=["Reviews"],
        summary="Update my review",
        description="Completely update an existing review. Only the owner can perform this action.",
    ),
    partial_update=extend_schema(
        tags=["Reviews"],
        summary="Partially update my review",
        description="Update specific fields of an existing review.",
    ),
    destroy=extend_schema(
        tags=["Reviews"],
        summary="Delete my review",
        description="Remove a review permanently from the system.",
    ),
    create=extend_schema(exclude=True),
)
