from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver

from users.models import UserSubscription

from .models import Invoice


@receiver(post_save, sender=Invoice)
def deduct_credit_on_invoice_creation(sender, instance, created, **kwargs):

    if created:
        if hasattr(instance.user, "profile"):
            user_profile = instance.user.profile
            user_tier = instance.user.tier
            if user_tier == UserSubscription.Tier.COMMUNITY:
                user_profile.credit_points = F("credit_points") - 1
                user_profile.save(update_fields=["credit_points"])
