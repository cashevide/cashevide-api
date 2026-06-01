from django.db import models

from core.models import BaseModel


class LegalDocument(BaseModel):
    class DocumentType(models.TextChoices):
        TERMS = "TERMS", "Terms and Conditions"
        PRIVACY = "PRIVACY", "Privacy Policy"

    document_type = models.CharField(max_length=20, choices=DocumentType.choices)
    version = models.CharField(max_length=10)
    content = models.TextField()
    effective_date = models.DateField()

    class Meta:
        ordering = ["-effective_date", "-created_at"]
        unique_together = ["document_type", "version"]

    def __str__(self):
        return f"{self.get_document_type_display()} - v{self.version}"  # type: ignore

    def save(self, *args, **kwargs):
        if self.is_active:
            LegalDocument.objects.filter(
                document_type=self.document_type, is_active=True
            ).exclude(id=self.id).update(is_active=False)  # type: ignore

        return super().save(*args, **kwargs)
