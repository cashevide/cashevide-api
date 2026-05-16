from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsOwner, IsSuperUser

from .models import Review, ReviewedClient, Tag
from .schema import (
    CLIENT_LOOKUP_SCHEMA,
    CLIENT_VIEWSET_SCHEMA,
    REVIEW_VIEWSET_SCHEMA,
    TAG_VIEWSET_SCHEMA,
    USER_REVIEW_VIEWSET_SCHEMA,
)
from .serializers import (
    ClientLookupSerializer,
    ReviewedClientSerializer,
    ReviewListSerializer,
    ReviewSerializer,
    TagSerializer,
    UserReviewListSerializer,
    UserReviewSerializer,
)
from .utils import hash_phone_number


@TAG_VIEWSET_SCHEMA
class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None

    def get_permissions(self):
        if self.action == "list":
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsSuperUser]

        return [permission() for permission in permission_classes]


@CLIENT_VIEWSET_SCHEMA
class ReviewedClientViewSet(viewsets.ModelViewSet):
    queryset = ReviewedClient.objects.all().order_by("-created_at")
    serializer_class = ReviewedClientSerializer

    def get_permissions(self):
        if self.action in ["create"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsSuperUser]

        return [permission() for permission in permission_classes]

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


@CLIENT_LOOKUP_SCHEMA
class ClientLookupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ClientLookupSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data["phone_number"]

        try:
            hashed_number = hash_phone_number(phone_number)
            client = get_object_or_404(ReviewedClient, phone_number=hashed_number)

            return Response(
                {"client_id": client.id, "message": "Client found successfully"},
                status=status.HTTP_200_OK,
            )

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception:
            return Response(
                {"error": "client not found"}, status=status.HTTP_404_NOT_FOUND
            )


@REVIEW_VIEWSET_SCHEMA
class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ["list", "create", "summary"]:
            permission_classes = [IsAuthenticated]

        else:
            permission_classes = [IsSuperUser]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        client_id = self.kwargs["client_id"]
        queryset = Review.objects.filter(
            client__id=client_id, client__is_active=True
        ).order_by("-created_at")

        if self.request.user.is_authenticated and getattr(
            self.request.user, "is_superuser", False
        ):
            return queryset

        return queryset.filter(is_active=True)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return ReviewListSerializer
        return ReviewSerializer

    def perform_create(self, serializer):
        client_id = self.kwargs["client_id"]
        client = get_object_or_404(ReviewedClient, id=client_id)

        return serializer.save(author=self.request.user, client=client)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

    @action(detail=False, methods=["get"])
    def summary(self, request, client_id=None):
        queryset = self.get_queryset()

        if not queryset.exists():
            return Response(
                {
                    "average_rating": 0,
                    "total_reviews": 0,
                    "rating_distribution": {5: 0, 4: 0, 3: 0, 2: 0, 1: 0},
                    "tags_summary": [],
                }
            )

        stats = queryset.aggregate(avg_rating=Avg("ratings"), total=Count("id"))

        rating_counts = queryset.values("ratings").annotate(count=Count("id"))

        distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
        for rc in rating_counts:
            if rc["ratings"]:
                distribution[rc["ratings"]] = rc["count"]

        tags = (
            Tag.objects.filter(reviews__in=queryset)
            .annotate(count=Count("reviews"))
            .values("id", "name", "category", "group", "count")
            .order_by("-count")
        )

        data = {
            "average_rating": round(stats["avg_rating"], 1)
            if stats["avg_rating"]
            else 0,
            "total_reviews": stats["total"],
            "rating_distribution": distribution,
            "tags_summary": list(tags),
        }

        return Response(data)


@USER_REVIEW_VIEWSET_SCHEMA
class UserReviewViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = UserReviewListSerializer

    def get_queryset(self):
        return Review.objects.filter(
            author=self.request.user, client__is_active=True
        ).order_by("-created_at")

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return UserReviewListSerializer
        return UserReviewSerializer

    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Use client endpoint to create reviews."},
            status=status.HTTP_400_BAD_REQUEST,
        )
