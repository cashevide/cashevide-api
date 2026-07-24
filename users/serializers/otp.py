from django.core.cache import cache
from rest_framework import serializers

from users.models import User


class BaseOTPVerificationSerializer(serializers.Serializer):
    """Serializer for verifying the OTP"""

    cache_prefix = None

    otp = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(write_only=True, required=True)

    def validate(self, attrs):
        otp = attrs.get("otp")
        email = attrs.get("email")

        cached_otp = cache.get(f"{self.cache_prefix}_otp_{email}")
        if not cached_otp:
            raise serializers.ValidationError(
                {
                    "otp": (
                        "The OTP has expired or does not exist. "
                        "Please request a new one."
                    )
                }
            )
        if cached_otp != otp:
            old_attempts = cache.get(f"{self.cache_prefix}_attempts_{email}")
            if old_attempts is None:
                old_attempts = 0

            new_attempts = old_attempts + 1

            cache.set(
                f"{self.cache_prefix}_attempts_{email}", value=new_attempts, timeout=300
            )

            if new_attempts >= 5:
                cache.delete(f"{self.cache_prefix}_otp_{email}")
                cache.delete(f"{self.cache_prefix}_attempts_{email}")

                raise serializers.ValidationError(
                    {"otp": "Too many attempts. OTP blocked. Please request a new OTP."}
                )

            remaining = 5 - new_attempts
            attempt_word = "attempt" if remaining == 1 else "attempts"
            raise serializers.ValidationError(
                {
                    "otp": (
                        "The provided OTP is invalid. "
                        f"{remaining} {attempt_word} remaining."
                    )
                }
            )

        cache.set(f"{self.cache_prefix}_verified_{email}", True, timeout=900)
        cache.delete(f"{self.cache_prefix}_otp_{email}")
        cache.delete(f"{self.cache_prefix}_attempts_{email}")

        return attrs


class SignupOTPRequestSerializer(serializers.Serializer):
    """Serializer for requesting an OTP"""

    email = serializers.EmailField(required=True, write_only=True)

    def validate_email(self, email):
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                "An account with this email address already exists."
            )

        return email


class SignupOTPVerificationSerializer(BaseOTPVerificationSerializer):
    cache_prefix = "signup"


class PasswordResetOTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)


class PasswordResetVerificationSerializer(BaseOTPVerificationSerializer):
    cache_prefix = "password_reset"
