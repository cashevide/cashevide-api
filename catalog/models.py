from django.conf import settings
from django.db import models

from core.models import BaseModel
from core.utils import generate_unique_slug


class Product(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="products"
    )
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, default="")

    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    slug = models.SlugField(unique=True, blank=True)

    is_archived = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Product, self.title)
        super().save(*args, **kwargs)
