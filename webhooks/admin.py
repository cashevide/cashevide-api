from django.contrib import admin

from .models import SESNotificationLog, SuppressedEmail


@admin.register(SuppressedEmail)
class SuppressedEmailAdmin(admin.ModelAdmin):
    list_display = ("email", "reason", "created_at")
    list_filter = ("reason",)
    search_fields = ("email",)
    ordering = ("-created_at",)


@admin.register(SESNotificationLog)
class SESNotificationLogAdmin(admin.ModelAdmin):
    list_display = ("notification_type", "created_at")
    list_filter = ("notification_type",)
    ordering = ("-created_at",)
    readonly_fields = ("notification_type", "raw_payload", "created_at", "updated_at")
