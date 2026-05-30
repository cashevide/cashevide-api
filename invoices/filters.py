import django_filters

from .models import Invoice


class InvoiceFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name="status")
    client = django_filters.NumberFilter(field_name="client_id")
    currency = django_filters.CharFilter(field_name="currency")

    from_issue_date = django_filters.DateFilter(
        field_name="issue_date", lookup_expr="gte"
    )
    to_issue_date = django_filters.DateFilter(
        field_name="issue_date", lookup_expr="lte"
    )

    from_due_date = django_filters.DateFilter(field_name="due_date", lookup_expr="gte")
    to_due_date = django_filters.DateFilter(field_name="due_date", lookup_expr="lte")

    class Meta:
        model = Invoice
        fields = ["status", "client", "currency"]
