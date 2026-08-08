from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver

from users.models import UserSubscription

from .models import Invoice

ENABLE_CREDIT_DEDUCTION = False


@receiver(post_save, sender=Invoice)
def deduct_credit_on_invoice_creation(sender, instance, created, **kwargs):

    if not ENABLE_CREDIT_DEDUCTION or not created:
        return

    if not hasattr(instance.user, "profile"):
        return

    if instance.user.tier == UserSubscription.Tier.COMMUNITY:
        user_profile = instance.user.profile
        user_profile.credit_points = F("credit_points") - 1
        user_profile.save(update_fields=["credit_points"])
