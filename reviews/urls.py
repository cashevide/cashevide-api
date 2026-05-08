from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ClientLookupView,
    ReviewedClientViewSet,
    ReviewViewSet,
    TagViewSet,
    UserReviewViewSet,
)

router = DefaultRouter()
router.register(r"reviewed-clients", ReviewedClientViewSet)
router.register(r"tags", TagViewSet)
router.register(r"my-reviews", UserReviewViewSet, basename="my-reviews")

urlpatterns = [
    path("", include(router.urls)),
    path("client-lookup/", ClientLookupView.as_view(), name="client_lookup"),
    path(
        "reviewed-client/<uuid:client_id>/reviews/",
        ReviewViewSet.as_view({"get": "list", "post": "create"}, name="client_review"),
    ),
    path(
        "reviewed-client/<uuid:client_id>/reviews/summary/",
        ReviewViewSet.as_view({"get": "summary"}, name="client_review_summary"),
    ),
    path(
        "reviewed-client/<uuid:client_id>/reviews/<int:pk>/",
        ReviewViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            },
            name="client_detail",
        ),
    ),
]
