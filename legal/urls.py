from django.urls import path

from .views import AcceptLegalDocumentsView, LatestLegalDocumentView

urlpatterns = [
    path("accept/", AcceptLegalDocumentsView.as_view(), name="accept_legal_documents"),
    path(
        "<str:doc_type>/",
        LatestLegalDocumentView.as_view(),
        name="latest-legal-document",
    ),
]
