from django.urls import path

from .views import LatestLegalDocumentView

urlpatterns = [
    path(
        "<str:doc_type>/",
        LatestLegalDocumentView.as_view(),
        name="latest-legal-document",
    )
]
