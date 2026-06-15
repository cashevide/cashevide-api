from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from legal.models import LegalDocument

from .models import User, UserBusinessProfile, UserProfile
from .services import create_user_account


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

            raise serializers.ValidationError(
                {"otp": "The provided OTP is invalid. Please try again."}
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


class UserProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)

    has_pending_agreements = serializers.SerializerMethodField()
    pending_legal_docs = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            "user_id",
            "email",
            "username",
            "full_name",
            "profile_picture",
            "phone_number",
            "job_title",
            "referral_code",
            "referred_by",
            "credit_points",
            "has_pending_agreements",
            "pending_legal_docs",
        ]

        read_only_fields = [
            "referral_code",
            "referred_by",
            "credit_points",
            "has_pending_agreements",
            "pending_legal_docs",
        ]

        extra_kwargs = {
            "full_name": {"required": True, "allow_blank": False},
        }

    def get_has_pending_agreements(self, obj):
        user = obj.user
        active_docs_count = LegalDocument.objects.filter(is_active=True).count()

        user_accepted_count = user.legal_document_acceptances.filter(
            legal_document__is_active=True
        ).count()

        return active_docs_count > user_accepted_count

    def get_pending_legal_docs(self, obj):
        user = obj.user

        if self.get_has_pending_agreements(obj):
            accepted_doc_ids = user.legal_document_acceptances.filter(
                legal_document__is_active=True
            ).values_list("legal_document_id", flat=True)

            pending_docs = LegalDocument.objects.filter(is_active=True).exclude(
                id__in=accepted_doc_ids
            )

            return [
                {
                    "id": doc.id,  # type:ignore
                    "doc_type": doc.document_type,
                    "version": doc.version,
                }
                for doc in pending_docs
            ]

        return []


class UserBusinessProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)

    class Meta:
        model = UserBusinessProfile
        fields = [
            "user_id",
            "business_name",
            "logo",
            "gst_number",
            "vat_number",
            "address",
            "phone_number",
            "website",
            "currency",
        ]

        extra_kwargs = {
            "business_name": {"required": True, "allow_blank": False},
            "address": {"required": True, "allow_blank": False},
            "phone_number": {"required": True, "allow_blank": False},
            "currency": {"required": True, "allow_blank": False},
        }


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


class PasswordResetOTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)


class PasswordResetVerificationSerializer(BaseOTPVerificationSerializer):
    cache_prefix = "password_reset"


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
