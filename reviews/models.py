import uuid

import phonenumbers
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.models import BaseModel

from .utils import hash_phone_number


class ReviewedClient(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        if not self.phone_number.startswith("sha256$"):
            try:
                self.phone_number = hash_phone_number(self.phone_number)
            except (phonenumbers.NumberParseException, ValueError) as e:
                raise ValidationError(f"Invalid phone number: {e}") from e

        super().save(*args, **kwargs)


class Tag(BaseModel):
    class TagCategory(models.TextChoices):
        POSITIVE = "POSITIVE", "Positive"
        NEGATIVE = "NEGATIVE", "Negative"

    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=TagCategory.choices)
    group = models.CharField(
        max_length=50, help_text="Tags with the same group are mutually exclusive"
    )

    def __str__(self):
        return self.name


class Review(BaseModel):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    tags = models.ManyToManyField(Tag, related_name="reviews")
    ratings = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating must be between 1 and 5",
    )
    client = models.ForeignKey(
        ReviewedClient, on_delete=models.CASCADE, related_name="reviews"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["author", "client"], name="unique_review_per_client"
            )
        ]

    def __str__(self):
        return f"{self.client} - {self.author}"
