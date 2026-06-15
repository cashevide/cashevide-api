from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from rest_framework import serializers

from users.models import User, UserProfile
from users.services import create_user_account


class GoogleAuthSerializer(serializers.Serializer):
    google_id_token = serializers.CharField(write_only=True, required=True)
    platform = serializers.ChoiceField(
        choices=["web", "mobile"], default="mobile", write_only=True, required=False
    )
    referral_code_input = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    username = serializers.CharField(
        required=False, allow_blank=False, allow_null=False
    )

    def validate_referral_code_input(self, value):
        if not value:
            return value

        try:
            self.referrer_profile = UserProfile.objects.get(referral_code=value)

        except UserProfile.DoesNotExist:
            raise serializers.ValidationError(
                "The referral code provided is incorrect. Please check it."
            )

        return value

    def validate_username(self, value):
        if value:
            if User.objects.filter(username__iexact=value).exists():
                raise serializers.ValidationError(
                    "This username is already taken. Please choose another one."
                )

        return value


class UserDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(write_only=True, required=True)
    referral_code_input = serializers.CharField(
        write_only=True, required=True, allow_blank=False, allow_null=False
    )
    platform = serializers.ChoiceField(
        choices=["web", "mobile"], default="mobile", write_only=True, required=False
    )
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "password",
            "full_name",
            "referral_code_input",
            "platform",
        ]

    def validate_referral_code_input(self, value):
        try:
            self.referrer_profile = UserProfile.objects.get(referral_code=value)

        except UserProfile.DoesNotExist:
            raise serializers.ValidationError(
                "The referral code provided is incorrect. Please check it."
            )
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        email = attrs.get("email")

        is_verified = cache.get(f"signup_verified_{email}")

        if not is_verified:
            raise serializers.ValidationError(
                {
                    "email": "This email address has not been verified. Please verify it using an OTP first."
                }
            )

        return attrs

    def create(self, validated_data):
        referrer_profile = getattr(self, "referrer_profile", None)
        return create_user_account(validated_data, referrer_profile=referrer_profile)


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)
    platform = serializers.ChoiceField(
        choices=["web", "mobile"], default="mobile", required=False
    )

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(email=email, password=password)
        if user and user.is_active:
            attrs["user"] = user
            return attrs
        raise serializers.ValidationError("Incorrect credentials!")
