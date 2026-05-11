from django.db import models

from core.models import BaseModel
from core.utils import generate_unique_slug


class Book(BaseModel):
    name = models.CharField(max_length=100, default="")
    price = models.PositiveSmallIntegerField(blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):

        if not self.slug:
            self.slug = generate_unique_slug(Book, self.name)

        super().save(*args, **kwargs)
