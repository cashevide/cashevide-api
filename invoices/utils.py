import datetime
from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone
from rest_framework.renderers import BaseRenderer


class PDFRenderer(BaseRenderer):
    media_type = "application/pdf"
    format = "pdf"
    charset = None
    render_style = "binary"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data


class DashboardDates:
    def __init__(self):
        self.today = timezone.now().date()

        self.current_month = self.today.month
        self.current_year = self.today.year
        self.last_year = self.current_year - 1

        if self.current_month == 1:
            self.last_month = 12
            self.last_month_year = self.current_year - 1
        else:
            self.last_month = self.current_month - 1
            self.last_month_year = self.current_year

        self.first_day_current_month = self.today.replace(day=1)
        self.end_date_3_months = self.first_day_current_month - timedelta(days=1)

        self.start_month = self.current_month - 3
        self.start_year = self.current_year
        if self.start_month <= 0:
            self.start_month += 12
            self.start_year -= 1

        self.start_date_3_months = datetime.date(self.start_year, self.start_month, 1)


def format_by_currency(queryset, currency_field="invoice__currency"):
    result = {}
    for item in queryset:
        currency_code = item[currency_field] or "UNKNOWN"
        result[currency_code] = item["total"] or Decimal("0.00")

    return result


def get_totals_by_currency(
    queryset, group_field="invoice__currency", sum_field="amount", **kwargs
):
    return queryset.filter(**kwargs).values(group_field).annotate(total=Sum(sum_field))
