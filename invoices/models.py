from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, GeneratedField, Sum

from catalog.models import Product
from clients.models import Client
from core.models import BaseModel
from users.models import UserSubscription


class Invoice(BaseModel):
    class InvoiceStatus(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        UNPAID = "UNPAID", "Unpaid"
        PARTIALLY_PAID = "PARTIALLY_PAID", "Partially Paid"
        PAID = "PAID", "Paid"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="invoices"
    )

    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        related_name="invoices",
        null=True,
        blank=True,
    )

    name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True, default="")

    business_snapshot = models.JSONField(default=dict, blank=True)

    invoice_number = models.CharField(max_length=50, blank=True)

    status = models.CharField(
        max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.DRAFT
    )

    currency = models.CharField(max_length=3, blank=True)

    issue_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)

    subtotal = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    discount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )

    amount_paid = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )

    balance_due = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )

    template = models.CharField(max_length=20, default="classic")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "invoice_number"], name="unique_invoice_per_user"
            )
        ]

    def __str__(self) -> str:
        return f"{self.invoice_number} - {self.name or 'Draft'}"

    def save(self, *args, **kwargs):
        self.clean()

        if hasattr(self.user, "business_profile"):
            bp = self.user.business_profile

            if not self.currency:
                self.currency = bp.currency

            if not self.business_snapshot:
                self.business_snapshot = {
                    "business_name": bp.business_name,
                    "logo": bp.logo.url if bp.logo else "",
                    "gst_number": bp.gst_number,
                    "vat_number": bp.vat_number,
                    "address": bp.address,
                    "phone_number": bp.phone_number,
                    "business_email": bp.business_email,
                    "website": bp.website,
                }
        else:
            self.currency = ""

        if not self.invoice_number:
            last_invoice = (
                Invoice.objects.filter(
                    user=self.user, invoice_number__startswith="INV-"
                )
                .order_by("id")
                .last()
            )
            if not last_invoice:
                self.invoice_number = "INV-0001"
            else:
                try:
                    last_number_str = last_invoice.invoice_number.split("-")[1]
                    new_number = int(last_number_str) + 1
                    self.invoice_number = f"INV-{new_number:04d}"
                except (IndexError, ValueError):
                    self.invoice_number = "INV-0001"

        if self.client:
            if not self.name:
                self.name = self.client.name

            if not self.email:
                self.email = self.client.email

            if not self.phone:
                self.phone = self.client.phone

            if not self.address:
                self.address = self.client.address

        super().save(*args, **kwargs)

    def clean(self) -> None:
        if not self.client and not self.name:
            raise ValidationError("Please select a client or provide a client name.")

        if not self.pk:
            if (
                hasattr(self.user, "profile")
                and hasattr(self.user, "subscription")
                and self.user.tier == UserSubscription.Tier.COMMUNITY
                and self.user.profile.credit_points <= 0
            ):
                raise ValidationError(
                    "You do not have enough credit points to create a new invoice."
                )

    def update_financials(self):
        items_sum = self.items.aggregate(total_sum=Sum("total"))[  # type:ignore
            "total_sum"
        ] or Decimal("0.00")
        self.subtotal = items_sum

        self.total_amount = self.subtotal - self.discount

        payment_sum = (
            self.payments.aggregate(paid_sum=Sum("amount"))["paid_sum"]  # type:ignore
            or Decimal("0.00")
        )

        self.amount_paid = payment_sum

        self.balance_due = max(Decimal("0.00"), self.total_amount - self.amount_paid)

        if self.amount_paid >= self.total_amount and self.total_amount > 0:
            self.status = self.InvoiceStatus.PAID
        elif self.amount_paid > 0:
            self.status = self.InvoiceStatus.PARTIALLY_PAID
        elif self.total_amount > 0:
            self.status = self.InvoiceStatus.UNPAID
        else:
            self.status = self.InvoiceStatus.DRAFT

        self.save(
            update_fields=[
                "subtotal",
                "total_amount",
                "amount_paid",
                "balance_due",
                "status",
            ]
        )


class InvoiceItem(BaseModel):
    class UnitType(models.TextChoices):
        QUANTITY = "QTY", "Quantity"
        HOURS = "HRS", "Hours"
        DAYS = "DAYS", "Days"

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, blank=True, null=True
    )

    title = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=255, blank=True, default="")

    unit_type = models.CharField(
        max_length=4, choices=UnitType.choices, default=UnitType.QUANTITY
    )

    quantity = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("1.00")
    )

    unit_price = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True
    )

    total = GeneratedField(
        expression=F("quantity") * F("unit_price"),
        output_field=models.DecimalField(max_digits=12, decimal_places=2),
        db_persist=True,
    )

    def __str__(self) -> str:
        return f"{self.title}(x{self.quantity})"

    def save(self, *args, **kwargs):
        self.clean()
        if self.product:
            if not self.title:
                self.title = self.product.title

            if not self.description:
                self.description = self.product.description

            if self.unit_price is None:
                self.unit_price = self.product.unit_price

        super().save(*args, **kwargs)
        self.invoice.update_financials()

    def delete(self, *args, **kwargs):
        invoice = self.invoice
        result = super().delete(*args, **kwargs)
        invoice.update_financials()
        return result

    def clean(self) -> None:
        if not self.product:
            if not self.title:
                raise ValidationError("Please select a product or provide a title.")

            if self.unit_price is None:
                raise ValidationError(
                    "Please select a product or provide a unit price."
                )


class PaymentRecord(BaseModel):
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="payments"
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    payment_date = models.DateField()

    payment_method = models.CharField(max_length=50, blank=True, default="")

    note = models.CharField(max_length=255, blank=True, default="")

    def __str__(self) -> str:
        return f"{self.invoice.invoice_number} - {self.amount} on {self.payment_date}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.invoice.update_financials()

    def delete(self, *args, **kwargs):
        invoice = self.invoice
        result = super().delete(*args, **kwargs)
        invoice.update_financials()
        return result
