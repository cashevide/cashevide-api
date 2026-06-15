from rest_framework import serializers

from legal.models import LegalDocument
from users.models import UserBusinessProfile, UserProfile


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
