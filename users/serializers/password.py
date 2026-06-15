from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from users.models import User


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    refresh = serializers.CharField(write_only=True, required=False)

    def validate_current_password(self, value):

        user = self.context["request"].user

        if not user.check_password(value):
            raise serializers.ValidationError({"detail": "Invalid current password."})

        return value

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    new_password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )

    def validate_email(self, value):

        is_verified = cache.get(f"password_reset_verified_{value}")

        if not is_verified:
            raise serializers.ValidationError(
                "This email address has not been verified. Please verify it using an OTP first."
            )
        return value

    def save(self, **kwargs):
        email = self.validated_data["email"]
        user = get_object_or_404(User, email=email)
        user.set_password(self.validated_data["new_password"])
        user.save()

        if email:
            cache.delete(f"password_reset_verified_{email}")

        return user
