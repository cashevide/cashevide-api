from django.http import HttpResponse
from django.template.loader import render_to_string
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from weasyprint import HTML

from .filters import InvoiceFilter
from .models import Invoice, PaymentRecord
from .schema import INVOICE_VIEWSET_SCHEMA
from .serializers import InvoiceSerialzer
from .utils import (
    DashboardDates,
    PDFRenderer,
    format_revenue_summary,
    get_revenue_by_currency,
)


@INVOICE_VIEWSET_SCHEMA
class InvoiceViewSet(ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerialzer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    filterset_class = InvoiceFilter

    search_fields = ["invoice_number", "name", "email", "phone"]

    ordering_fields = [
        "issue_date",
        "due_date",
        "total_amount",
        "balance_due",
        "created_at",
    ]

    ordering = ["-created_at"]

    actions_to_filter = [
        "list",
        "retrieve",
        "update",
        "partial_update",
        "destroy",
        "dashboard_analytics",
        "download_pdf",
    ]

    def get_queryset(self):
        queryset = super().get_queryset().filter(user=self.request.user)

        if self.action in self.actions_to_filter:
            return queryset.filter(is_active=True)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(
        detail=True,
        methods=["get"],
        url_path="download-pdf",
        renderer_classes=[PDFRenderer],
    )
    def download_pdf(self, request, pk=None):
        invoice = self.get_object()
        user = request.user

        business_profile = getattr(user, "business_profile", None)

        context = {
            "invoice": invoice,
            "items": invoice.items.all(),
            "business_profile": business_profile,
        }

        html_string = render_to_string("invoices/invoice_pdf.html", context)

        pdf_file = HTML(
            string=html_string, base_url=request.build_absolute_uri()
        ).write_pdf()

        response = HttpResponse(pdf_file, content_type="application/pdf")

        response["Content-Disposition"] = (
            f'attachment; filename="Invoice_{invoice.invoice_number}.pdf"'
        )

        return response

    @action(detail=False, methods=["get"], url_path="dashboard-analytics")
    def dashboard_analytics(self, request):

        user = request.user
        payment_records = PaymentRecord.objects.filter(
            invoice__user=user,
            invoice__is_active=True,
            is_active=True,
        )
        dates = DashboardDates()

        data = {
            "total_revenue": format_revenue_summary(
                revenue_queryset=get_revenue_by_currency(payment_records)
            ),
            "revenue_this_month": format_revenue_summary(
                revenue_queryset=get_revenue_by_currency(
                    payment_records,
                    payment_date__month=dates.current_month,
                    payment_date__year=dates.current_year,
                )
            ),
            "revenue_last_month": format_revenue_summary(
                revenue_queryset=get_revenue_by_currency(
                    payment_records,
                    payment_date__month=dates.last_month,
                    payment_date__year=dates.last_month_year,
                )
            ),
            "revenue_last_three_months": format_revenue_summary(
                revenue_queryset=get_revenue_by_currency(
                    payment_records,
                    payment_date__range=(
                        dates.start_date_3_months,
                        dates.end_date_3_months,
                    ),
                )
            ),
            "revenue_this_year": format_revenue_summary(
                revenue_queryset=get_revenue_by_currency(
                    payment_records,
                    payment_date__year=dates.current_year,
                )
            ),
        }

        return Response(data)

    def perform_destroy(self, instance) -> None:
        instance.is_active = False
        instance.save()
