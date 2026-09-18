from django.urls import path

from .views import SESNotificationWebhookView

urlpatterns = [
    path(
        "ses-notifications/",
        SESNotificationWebhookView.as_view(),
        name="ses-notifications-webhook",
    ),
]
