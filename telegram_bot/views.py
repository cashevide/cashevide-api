import requests
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


class TelegramWebhookAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):

        update = request.data

        if "message" in update:
            chat_id = update["message"]["chat"]["id"]
            text = update["message"].get("text", "").strip()

            if text == "/start":
                payload = {
                    "chat_id": chat_id,
                    "text": "hai",
                }

                try:
                    requests.post(TELEGRAM_API_URL, json=payload, timeout=10)

                except Exception as e:
                    print(f"Telegram Error: {e}")

        return Response({"status": "ok"}, status=status.HTTP_200_OK)
