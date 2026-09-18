from django.db import models

from core.models import BaseModel


class SuppressedEmail(models.Model):
    class Reason(models.TextChoices):
        BOUNCE = "BOUNCE", "Bounce"
        COMPLAINT = "COMPLAINT", "Complaint"

    email = models.EmailField(unique=True, db_index=True)
    reason = models.CharField(max_length=20, choices=Reason.choices)
    detail = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} ({self.reason})"


class SESNotificationLog(BaseModel):
    """
    Raw log of every SNS notification received, for debugging/audit.
    """

    notification_type = models.CharField(max_length=50)
    raw_payload = models.JSONField()

    def __str__(self):
        return f"{self.notification_type} @ {self.created_at}"
