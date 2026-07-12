import socket
from urllib.parse import urlparse

import requests
import tldextract
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
REFERRAL_CODE = settings.TELEGRAM_REFERRAL_CODE
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


EXCLUDE_LIST = {
    "google.com",
    "bing.com",
    "duckduckgo.com",
    "yahoo.com",
    "facebook.com",
    "instagram.com",
    "x.com",
    "twitter.com",
    "tiktok.com",
    "threads.net",
    "reddit.com",
    "snapchat.com",
    "pinterest.com",
    "youtube.com",
    "youtu.be",
    "vimeo.com",
    "twitch.tv",
    "wikipedia.org",
    "quora.com",
    "bbc.com",
    "bbc.co.uk",
    "cnn.com",
    "reuters.com",
    "ndtv.com",
    "indiatoday.in",
    "thehindu.com",
    "chatgpt.com",
    "openai.com",
    "gemini.google.com",
    "claude.ai",
}


def domain_exists(domain: str) -> bool:
    try:
        socket.getaddrinfo(domain, None)
        return True
    except socket.gaierror:
        return False


def validate_profile_link(text: str) -> bool:
    url = text.strip().lower()

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    domain = urlparse(url).hostname

    if not domain:
        return False

    if not tldextract.extract(domain).suffix:
        return False

    for exclude in EXCLUDE_LIST:
        if domain == exclude or domain.endswith(f".{exclude}"):
            return False

    if not domain_exists(domain):
        return False

    return True


class TelegramWebhookAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):

        update = request.data
        message = update.get("message")

        if message:
            chat_id = message.get("chat", {}).get("id")
            name = message.get("from", {}).get("first_name", "there")
            text = message.get("text", "").strip()
            text_lower = text.lower()

            if chat_id:
                reply_markup = None

                # 1. When the user clicks the 'Start' button for the first time
                if text_lower == "/start":
                    reply = (
                        f"👋 *Hi {name}!*\n\n"
                        "Send your LinkedIn, GitHub, Behance, or portfolio link "
                        "to get your *Referral Code*.\n\n"
                    )

                # 2. Check if the input contains a valid profile link
                elif validate_profile_link(text_lower):
                    # Fallback safety check for referral code
                    if REFERRAL_CODE:
                        reply = (
                            "✅ Profile verified!\n\n"
                            "Your referral code:\n\n"
                            f"*{REFERRAL_CODE}*\n\n"
                            "Tap the button below to copy it and use it during signup."
                        )

                        reply_markup = {
                            "inline_keyboard": [
                                [
                                    {
                                        "text": "Copy Referral Code",
                                        "copy_text": {"text": REFERRAL_CODE},
                                    }
                                ]
                            ]
                        }

                    else:
                        reply = (
                            "⚠️ Referral codes are temporarily unavailable.\n\n"
                            "Please try again later."
                        )

                # 3. Fallback for messages without a valid link
                else:
                    reply = (
                        "❌ I couldn't find a valid profile link.\n\n"
                        "Send your LinkedIn, GitHub, Behance, or portfolio link.\n\n"
                    )

                payload = {
                    "chat_id": chat_id,
                    "text": reply,
                    "parse_mode": "Markdown",
                }

                if reply_markup:
                    payload["reply_markup"] = reply_markup

                try:
                    requests.post(TELEGRAM_API_URL, json=payload, timeout=10)

                except Exception as e:
                    print(f"Telegram Error: {e}")

        return Response({"status": "ok"}, status=status.HTTP_200_OK)
