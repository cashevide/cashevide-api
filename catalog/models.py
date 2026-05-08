from django.conf import settings
from django.db import models

from core.models import BaseModel


class Product(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="products"
    )
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, default="")

    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.title
