from django.contrib import admin

from .models import LegalDocument, UserLegalDocumentAcceptance

admin.site.register(LegalDocument)


@admin.register(UserLegalDocumentAcceptance)
class UserLegalDocumentAcceptanceAdmin(admin.ModelAdmin):
    list_display = ("user_email", "document_type", "version", "accepted_at")
    list_filter = ("legal_document__document_type", "accepted_at")

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "User Email"  # type: ignore

    def document_type(self, obj):
        return obj.legal_document.get_document_type_display()

    document_type.short_description = "Document Type"  # type: ignore

    def version(self, obj):
        return f"v{obj.legal_document.version}"

    version.short_description = "Version"  # type: ignore
