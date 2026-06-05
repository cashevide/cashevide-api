from django.core.cache import cache
from django.db import transaction
from django.db.models import F

from .models import User, UserBusinessProfile, UserProfile, UserSubscription
from .utils import generate_unique_referral_code

SIGNUP_BONUS_CREDITS = 20
REFEREE_BONUS_CREDITS = 20
REFERRER_BONUS_CREDITS = 30


@transaction.atomic
def create_user_account(validated_data, referrer_profile=None):

    email = validated_data.get("email")

    validated_data.pop("referral_code_input", None)
    full_name = validated_data.pop("full_name")
    validated_data.pop("platform", "mobile")

    user = User.objects.create_user(**validated_data)

    initial_credits = SIGNUP_BONUS_CREDITS
    referred_by_user = None

    if referrer_profile:
        initial_credits += REFEREE_BONUS_CREDITS
        referrer_profile.credit_points = F("credit_points") + REFERRER_BONUS_CREDITS
        referrer_profile.save(update_fields=["credit_points"])
        referred_by_user = referrer_profile.user

    referral_code = generate_unique_referral_code()

    UserProfile.objects.create(
        user=user,
        full_name=full_name,
        referral_code=referral_code,
        referred_by=referred_by_user,
        credit_points=initial_credits,
    )

    UserBusinessProfile.objects.create(user=user)
    UserSubscription.objects.create(user=user)

    if email:
        cache.delete(f"signup_otp_{email}")
        cache.delete(f"signup_verified_{email}")

    return user
