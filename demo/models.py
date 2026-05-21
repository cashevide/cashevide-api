from django.db import models


class Invoice(models.Model):
    name = models.CharField(max_length=50, default="")
    invoice_number = models.CharField(max_length=50)

    def __str__(self) -> str:
        return f"{self.name} - {self.invoice_number}"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    title = models.CharField(max_length=50, default="")

    def __str__(self) -> str:
        return f"{self.invoice.invoice_number} - {self.title}"


class PaymentRecord(models.Model):
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="payments"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.invoice.invoice_number} - {self.amount}"
