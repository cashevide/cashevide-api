from django.urls import path

from .views import TelegramWebhookAPIView

urlpatterns = [
    path("webhook/", TelegramWebhookAPIView.as_view(), name="telegram_webhook")
]
