from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email

    @property
    def tier(self):
        if hasattr(self, "subscription"):
            return self.subscription.tier  # type:ignore


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    profile_picture = models.ImageField(
        upload_to="profile_pictures/", null=True, blank=True
    )
    full_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20, blank=True, default="")
    job_title = models.CharField(max_length=100, blank=True, default="")
    referral_code = models.CharField(max_length=50, unique=True, db_index=True)
    referred_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="referrals",
    )
    credit_points = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.user.email


class UserBusinessProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="business_profile",
    )
    business_name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to="logos/", null=True, blank=True)
    gst_number = models.CharField(max_length=15, blank=True, default="")
    vat_number = models.CharField(max_length=15, blank=True, default="")
    address = models.TextField()
    phone_number = models.CharField(max_length=20)
    website = models.URLField(blank=True, default="")
    default_currency = models.CharField(max_length=3, default="INR")

    def __str__(self):
        return f"{self.user.email} - {self.business_name}"


class UserSubscription(models.Model):
    class Tier(models.TextChoices):
        SILVER = "SILVER", "Silver"
        GOLD = "GOLD", "Gold"
        PLATINUM = "PLATINUM", "Platinum"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription",
    )

    tier = models.CharField(max_length=20, choices=Tier.choices, default=Tier.SILVER)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.email} - {self.tier}"
