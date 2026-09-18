import json
import logging
import urllib.request

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SESNotificationLog, SuppressedEmail
from .sns_verification import verify_sns_message

logger = logging.getLogger(__name__)


class SESNotificationWebhookView(APIView):
    """
    Receives SNS notifications for Amazon SES bounces and complaints.

    SNS sends three kinds of message here:
      1. SubscriptionConfirmation - one-time, when the subscription is
         first created. We must hit the SubscribeURL to activate it.
      2. Notification - the actual bounce/complaint event.
      3. UnsubscribeConfirmation - if someone unsubscribes the endpoint.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body)
        except (json.JSONDecodeError, TypeError):
            return Response(
                {"error": "Invalid JSON payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not verify_sns_message(payload):
            logger.warning("Rejected SNS webhook call: signature verification failed.")
            return Response(
                {"error": "Signature verification failed."},
                status=status.HTTP_403_FORBIDDEN,
            )

        message_type = payload.get("Type")

        if message_type == "SubscriptionConfirmation":
            return self._handle_subscription_confirmation(payload)

        if message_type == "Notification":
            return self._handle_notification(payload)

        # UnsubscribeConfirmation or anything else - nothing to do,
        # just acknowledge so SNS doesn't retry.
        return Response({"status": "ignored"}, status=status.HTTP_200_OK)

    def _handle_subscription_confirmation(self, payload):
        subscribe_url = payload.get("SubscribeURL")

        if not subscribe_url:
            return Response(
                {"error": "Missing SubscribeURL."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            urllib.request.urlopen(subscribe_url, timeout=5)
        except Exception as e:
            logger.error(f"Failed to confirm SNS subscription: {e}")
            return Response(
                {"error": "Failed to confirm subscription."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info("SNS subscription confirmed successfully.")
        return Response({"status": "subscription confirmed"}, status=status.HTTP_200_OK)

    def _handle_notification(self, payload):
        try:
            message = json.loads(payload.get("Message", "{}"))
        except json.JSONDecodeError:
            return Response(
                {"error": "Invalid Message payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        notification_type = message.get("notificationType")

        SESNotificationLog.objects.create(
            notification_type=notification_type or "UNKNOWN",
            raw_payload=message,
        )

        if notification_type == "Bounce":
            self._process_bounce(message)
        elif notification_type == "Complaint":
            self._process_complaint(message)
        # "Delivery" and anything else: nothing to do, already logged above.

        return Response({"status": "processed"}, status=status.HTTP_200_OK)

    def _process_bounce(self, message):
        bounce = message.get("bounce", {})
        bounce_type = bounce.get("bounceType")  # "Permanent" or "Transient"

        # Only permanent bounces mean the address is genuinely bad.
        # Transient bounces (e.g. mailbox temporarily full) shouldn't
        # get the address suppressed forever.
        if bounce_type != "Permanent":
            return

        for recipient in bounce.get("bouncedRecipients", []):
            email = recipient.get("emailAddress")
            if not email:
                continue

            SuppressedEmail.objects.update_or_create(
                email=email,
                defaults={
                    "reason": SuppressedEmail.Reason.BOUNCE,
                    "detail": recipient.get("diagnosticCode", ""),
                },
            )
            logger.info(f"Suppressed email due to permanent bounce: {email}")

    def _process_complaint(self, message):
        complaint = message.get("complaint", {})

        for recipient in complaint.get("complainedRecipients", []):
            email = recipient.get("emailAddress")
            if not email:
                continue

            SuppressedEmail.objects.update_or_create(
                email=email,
                defaults={
                    "reason": SuppressedEmail.Reason.COMPLAINT,
                    "detail": complaint.get("complaintFeedbackType", ""),
                },
            )
            logger.info(f"Suppressed email due to complaint: {email}")
