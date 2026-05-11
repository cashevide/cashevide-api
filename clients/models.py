from django.conf import settings
from django.db import models

from core.models import BaseModel
from core.utils import generate_unique_slug


class Client(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="clients"
    )
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True, default="")
    slug = models.SlugField(unique=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Client, self.name)
        super().save(*args, **kwargs)
