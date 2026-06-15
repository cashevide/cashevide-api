import logging
import random
import secrets
import string

from django.conf import settings
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)


def set_auth_cookies(user, platform, refresh, access_token, is_signup):

    from .serializers import UserDetailSerializer

    status_code = status.HTTP_201_CREATED if is_signup else status.HTTP_200_OK
    message = "Signup successful" if is_signup else "login successful"

    payload = {"message": message, "user": UserDetailSerializer(user).data}

    if platform != "web":
        payload["access"] = access_token
        payload["refresh"] = str(refresh)

    response = Response(payload, status_code)

    if platform == "web":
        response.set_cookie(
            key="access_token",
            value=access_token,
            max_age=5 * 60,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
            domain=settings.COOKIE_DOMAIN,
        )
        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            max_age=90 * 24 * 60 * 60,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
            domain=settings.COOKIE_DOMAIN,
        )
    return response


def clear_auth_session(request, refresh_token=None, user=None):

    message = (
        "Account successfully deleted."
        if user
        else "Password has been updated successfully."
    )

    payload = {"message": message}

    if not refresh_token:
        refresh_token = request.COOKIES.get("refresh_token")

    if refresh_token:
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception as e:
            logger.error(f"Token blacklist failed during session clearance: {e}")
            pass

    if user:
        user.delete()

    response = Response(
        payload,
        status=status.HTTP_200_OK,
    )

    response.delete_cookie("access_token", domain=settings.COOKIE_DOMAIN)
    response.delete_cookie("refresh_token", domain=settings.COOKIE_DOMAIN)

    return response


def generate_unique_referral_code():
    from .models import UserProfile

    while True:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not UserProfile.objects.filter(referral_code=code).exists():
            return code


def generate_otp(length=6):
    upper_bound = 10**length
    return f"{secrets.randbelow(upper_bound):0{length}d}"


def send_otp_email(email, otp, purpose="signup"):
    subject = "Your Cashevide Verification Code"

    if purpose == "password_reset":
        message = (
            "Hello,"
            f"\n\nYour verification code for resetting your password is: {otp}"
            "\n\nThis code will expire in 5 minutes.\n\nThank you!"
        )
    else:
        message = (
            "Welcome to Cashevide!"
            f"\n\nYour verification code for signup is: {otp}\n\n"
            "This code will expire in 5 minutes.\n\nThank you!"
        )

    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]

    send_mail(
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=recipient_list,
        fail_silently=False,
    )
