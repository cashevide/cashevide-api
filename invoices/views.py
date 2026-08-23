from django.conf import settings
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
from .serializers import InvoiceSerializer
from .utils import (
    DashboardDates,
    PDFRenderer,
    format_by_currency,
    get_totals_by_currency,
)


@INVOICE_VIEWSET_SCHEMA
class InvoiceViewSet(ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
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

        fonts_dir = settings.BASE_DIR / "invoices" / "static" / "invoices" / "fonts"

        context = {
            "invoice": invoice,
            "items": invoice.items.all(),
            "business_profile": business_profile,
            "fonts_dir": f"file://{fonts_dir}",
        }

        html_string = render_to_string(f"invoices/{invoice.template}.html", context)

        pdf_file = HTML(
            string=html_string, base_url=request.build_absolute_uri()
        ).write_pdf()

        response = HttpResponse(pdf_file, content_type="application/pdf")

        content_disposition = "attachment"

        if settings.DEBUG:
            content_disposition = "inline"

        response["Content-Disposition"] = (
            f"{content_disposition}; "
            f'filename="{invoice.name}_{invoice.invoice_number}.pdf"'
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
        invoices = self.get_queryset()
        dates = DashboardDates()

        data = {
            "revenue": {
                "total": format_by_currency(
                    queryset=get_totals_by_currency(payment_records)
                ),
                "this_month": format_by_currency(
                    queryset=get_totals_by_currency(
                        payment_records,
                        payment_date__month=dates.current_month,
                        payment_date__year=dates.current_year,
                    )
                ),
                "last_month": format_by_currency(
                    queryset=get_totals_by_currency(
                        payment_records,
                        payment_date__month=dates.last_month,
                        payment_date__year=dates.last_month_year,
                    )
                ),
                "last_three_months": format_by_currency(
                    queryset=get_totals_by_currency(
                        payment_records,
                        payment_date__range=(
                            dates.start_date_3_months,
                            dates.end_date_3_months,
                        ),
                    )
                ),
                "this_year": format_by_currency(
                    queryset=get_totals_by_currency(
                        payment_records,
                        payment_date__year=dates.current_year,
                    )
                ),
                "last_year": format_by_currency(
                    queryset=get_totals_by_currency(
                        payment_records,
                        payment_date__year=dates.last_year,
                    )
                ),
            },
            "balance_due": {
                "total": format_by_currency(
                    queryset=get_totals_by_currency(
                        invoices, group_field="currency", sum_field="balance_due"
                    ),
                    currency_field="currency",
                ),
            },
        }

        return Response(data)

    def perform_destroy(self, instance) -> None:
        instance.is_active = False
        instance.save()
