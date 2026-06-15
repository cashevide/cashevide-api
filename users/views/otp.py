from django.core.cache import cache
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User
from users.schema import (
    OTP_REQUEST_SCHEMA,
    OTP_VERIFICATION_SCHEMA,
    PASSWORD_RESET_OTP_REQUEST_SCHEMA,
    PASSWORD_RESET_OTP_VERIFICATION_SCHEMA,
)
from users.serializers.otp import (
    PasswordResetOTPRequestSerializer,
    PasswordResetVerificationSerializer,
    SignupOTPRequestSerializer,
    SignupOTPVerificationSerializer,
)
from users.utils import (
    generate_otp,
    send_otp_email,
)


class BaseOTPRequestView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    otp_cache_prefix = None
    OTPRequestSerializer = None
    purpose = "signup"
    message = None

    def should_send_otp(self, email: str) -> bool:
        return True

    def post(self, request, *args, **kwargs):

        serializer = self.OTPRequestSerializer(data=request.data)  # type:ignore

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]

        if not self.should_send_otp(email):
            return Response(
                {"message": self.message},
                status=status.HTTP_200_OK,
            )

        otp = generate_otp()

        try:
            send_otp_email(email, otp, self.purpose)

            cache.set(f"{self.otp_cache_prefix}_otp_{email}", value=otp, timeout=300)
            cache.delete(f"{self.otp_cache_prefix}_attempts_{email}")

            return Response(
                {"message": self.message},
                status=status.HTTP_200_OK,
            )

        except Exception:
            return Response(
                {"error": "Failed to send the OTP. Please try again later."},
                status=status.HTTP_400_BAD_REQUEST,
            )


@OTP_REQUEST_SCHEMA
class SignupOTPRequestView(BaseOTPRequestView):
    otp_cache_prefix = "signup"
    OTPRequestSerializer = SignupOTPRequestSerializer
    message = "An OTP has been successfully sent to your email address."


@OTP_VERIFICATION_SCHEMA
class SignupOTPVerificationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = SignupOTPVerificationSerializer(data=request.data)

        if serializer.is_valid():
            return Response(
                {"message": "Email verification successful."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@PASSWORD_RESET_OTP_REQUEST_SCHEMA
class PasswordResetOTPRequestView(BaseOTPRequestView):
    otp_cache_prefix = "password_reset"
    OTPRequestSerializer = PasswordResetOTPRequestSerializer
    purpose = "password_reset"
    message = "If an account exists, an OTP has been sent."

    def should_send_otp(self, email: str) -> bool:
        return User.objects.filter(email=email).exists()


@PASSWORD_RESET_OTP_VERIFICATION_SCHEMA
class PasswordResetOTPVerificationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetVerificationSerializer(data=request.data)

        if serializer.is_valid():
            return Response(
                {"message": "Email verification successful."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
