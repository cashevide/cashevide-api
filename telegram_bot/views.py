import re

import requests
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
REFERRAL_CODE = settings.TELEGRAM_REFERRAL_CODE
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


def validate_profile_link(text: str) -> bool:
    """
    Smarter heuristic check using Regex to detect any valid URL structure
    or domain pattern (e.g., github.com, noufal.me, http://any-blog.xyz).
    """

    urlpattern = r"(https?://\S+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"

    return bool(re.search(urlpattern, text))


class TelegramWebhookAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):

        update = request.data

        if "message" in update:
            chat_id = update["message"]["chat"]["id"]
            name = update["message"]["from"]["first_name"]
            text = update["message"].get("text", "").strip()
            text_lower = text.lower()

            reply_markup = None

            # 1. When the user clicks the 'Start' button for the first time
            if text_lower == "/start":
                reply = (
                    f"*Hello {name}! Welcome to the Cashevide Assistant Bot.* 👋\n\n"
                    "To get your *referral code*, please share your LinkedIn, Behance, "
                    "GitHub, or personal portfolio link here. 🔗"
                )

            # 2. Check if the input contains a valid profile link
            elif validate_profile_link(text_lower):
                # Fallback safety check for referral code
                if REFERRAL_CODE:
                    reply = (
                        "🎉 *Your profile verification is complete!*\n\n"
                        "Here is your referral code to register on the app:\n\n"
                        f"`{REFERRAL_CODE}`\n\n"
                        "Copy this code and use it in the app. Welcome to Cashevide! 🤝"
                    )

                    reply_markup = {
                        "inline_keyboard": [
                            [
                                {
                                    "text": "Copy Referral Code 📋",
                                    "copy_text": {"text": REFERRAL_CODE},
                                }
                            ]
                        ]
                    }

                else:
                    reply = (
                        "⚠️ Sorry, referral codes are currently unavailable due to "
                        "technical reasons. Please try again later."
                    )

            # 3. Fallback for messages without a valid link
            else:
                reply = (
                    "Please send a valid profile link (LinkedIn/GitHub/Portfolio) "
                    "to receive your referral code. 😊"
                )

            payload = {
                "chat_id": chat_id,
                "text": reply,
                "parse_mode": "Markdown",  # Helps copy code with a single click
            }

            if reply_markup:
                payload["reply_markup"] = reply_markup

            try:
                requests.post(TELEGRAM_API_URL, json=payload, timeout=10)

            except Exception as e:
                print(f"Telegram Error: {e}")

        return Response({"status": "ok"}, status=status.HTTP_200_OK)
