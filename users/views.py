import logging

from django.conf import settings
from django.core.cache import cache
from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .models import User, UserBusinessProfile, UserProfile
from .schema import (
    GOOGLE_LOGIN_SCHEMA,
    OTP_REQUEST_SCHEMA,
    OTP_VERIFICATION_SCHEMA,
    PASSWORD_CHANGE_SCHEMA,
    PASSWORD_RESET_OTP_REQUEST_SCHEMA,
    PASSWORD_RESET_OTP_VERIFICATION_SCHEMA,
    PASSWORD_RESET_SCHEMA,
    TOKEN_REFRESH_SCHEMA,
    USER_BUSINESS_PROFILE_SCHEMA,
    USER_CHECK_FIELD_SCHEMA,
    USER_DELETE_SCHEMA,
    USER_LOGIN_SCHEMA,
    USER_LOGOUT_SCHEMA,
    USER_PROFILE_SCHEMA,
    USER_SIGNUP_SCHEMA,
)
from .serializers import (
    GoogleLoginSerializer,
    PasswordChangeSerializer,
    PasswordResetOTPRequestSerializer,
    PasswordResetSerializer,
    PasswordResetVerificationSerializer,
    SignupOTPRequestSerializer,
    SignupOTPVerificationSerializer,
    UserBusinessProfileSerializer,
    UserDetailSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
)
from .services import create_user_account
from .utils import clear_auth_session, generate_otp, send_otp_email, set_auth_cookies

logger = logging.getLogger(__name__)


class BaseOTPRequestView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    otp_cache_prefix = None
    OTPRequestSerializer = None
    purpose = "signup"

    def post(self, request, *args, **kwargs):

        serializer = self.OTPRequestSerializer(data=request.data)  # type:ignore
        if serializer.is_valid():
            email = serializer.validated_data.get("email")
            otp = generate_otp()

            try:
                send_otp_email(email, otp, self.purpose)
                cache.set(
                    f"{self.otp_cache_prefix}_otp_{email}", value=otp, timeout=300
                )
                return Response(
                    {
                        "message": "An OTP has been successfully "
                        "sent to your email address."
                    },
                    status=status.HTTP_200_OK,
                )

            except Exception:
                return Response(
                    {"error": "Failed to send the OTP. Please try again later."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@OTP_REQUEST_SCHEMA
class SignupOTPRequestView(BaseOTPRequestView):
    otp_cache_prefix = "signup"
    OTPRequestSerializer = SignupOTPRequestSerializer


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


@GOOGLE_LOGIN_SCHEMA
class GoogleLoginView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = GoogleLoginSerializer(data=request.data)

        if serializer.is_valid():
            google_id_token = serializer.validated_data.get("google_id_token")
            platform = serializer.validated_data.get("platform")
            referral_code_input = serializer.validated_data.get("referral_code_input")
            username = serializer.validated_data.get("username")

            try:
                id_info = id_token.verify_oauth2_token(
                    google_id_token,
                    requests.Request(),
                    settings.GOOGLE_CLIENT_ID,
                )

                email = id_info.get("email")
                first_name = id_info.get("given_name", "")
                last_name = id_info.get("family_name", "")

            except ValueError:
                return Response(
                    {"error": "Invalid or expired Google token."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = User.objects.filter(email=email).first()
            is_signup = False

            if not user:
                if not referral_code_input:
                    return Response(
                        {
                            "status": "prompt_referral",
                            "email": email,
                            "full_name": f"{first_name} {last_name}",
                        },
                        status=status.HTTP_200_OK,
                    )
                if not username:
                    return Response(
                        {"username": ["This field is required for new users."]},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                user_data = {
                    "email": email,
                    "username": username,
                    "full_name": f"{first_name} {last_name}",
                }
                referrer_profile = getattr(serializer, "referrer_profile", None)

                user = create_user_account(
                    validated_data=user_data, referrer_profile=referrer_profile
                )
                is_signup = True

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return set_auth_cookies(
                user=user,
                platform=platform,
                refresh=refresh,
                access_token=access_token,
                is_signup=is_signup,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@USER_SIGNUP_SCHEMA
class UserSignupView(CreateAPIView):
    serializer_class = UserDetailSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            platform = request.data.get("platform", "mobile")

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return set_auth_cookies(
                user=user,
                platform=platform,
                refresh=refresh,
                access_token=access_token,
                is_signup=True,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@USER_PROFILE_SCHEMA
class UserProfileView(RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


@USER_BUSINESS_PROFILE_SCHEMA
class UserBusinessProfileView(RetrieveUpdateAPIView):
    serializer_class = UserBusinessProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        profile, _ = UserBusinessProfile.objects.get_or_create(user=self.request.user)
        return profile


@USER_CHECK_FIELD_SCHEMA
class CheckFieldExistsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        field = request.query_params.get("field")
        value = request.query_params.get("value")

        if not field or not value:
            return Response(
                {"error": "Please provide both 'field' and 'value'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        allowed_fields = ["username", "email"]

        if field not in allowed_fields:
            return Response(
                {"error": f"Checking '{field}' is not allowed or invalid."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        filter_kwargs = {field: value}

        try:
            is_taken = User.objects.filter(**filter_kwargs).exists()
            return Response({"is_available": not is_taken})

        except Exception as e:
            logger.error(f"Error checking field {field}: {e}")
            return Response(
                {"error": "An unexpected error occurred. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@USER_LOGIN_SCHEMA
class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)

        if serializer.is_valid():
            validated_data = serializer.validated_data

            user = validated_data.get("user")
            platform = validated_data.get("platform", "mobile")

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return set_auth_cookies(
                user=user,
                platform=platform,
                refresh=refresh,
                access_token=access_token,
                is_signup=False,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@PASSWORD_CHANGE_SCHEMA
class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PasswordChangeSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()

            refresh_token = serializer.validated_data.get("refresh")

            return clear_auth_session(refresh_token=refresh_token, request=request)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@PASSWORD_RESET_OTP_REQUEST_SCHEMA
class PasswordResetOTPRequestView(BaseOTPRequestView):
    otp_cache_prefix = "password_reset"
    OTPRequestSerializer = PasswordResetOTPRequestSerializer
    purpose = "password_reset"


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


@PASSWORD_RESET_SCHEMA
class PasswordResetView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Password has been updated successfully."})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@USER_LOGOUT_SCHEMA
class LogoutView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response(
                {"error": "Refresh token is required to logout"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            response = Response(
                {"message": "Successfully logged out"}, status=status.HTTP_200_OK
            )
            response.delete_cookie("access_token", domain=settings.COOKIE_DOMAIN)
            response.delete_cookie("refresh_token", domain=settings.COOKIE_DOMAIN)
            return response

        except Exception:
            return Response(
                {"error": "Invalid or expired token"},
                status=status.HTTP_400_BAD_REQUEST,
            )


@TOKEN_REFRESH_SCHEMA
class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")
        platform = request.data.get("platform")

        if not refresh_token:
            refresh_token = request.COOKIES.get("refresh_token")
            if refresh_token and not platform:
                platform = "web"

        if not platform:
            platform = "mobile"

        if not refresh_token:
            return Response(
                {"error": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = {"refresh": refresh_token}
        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response(
                {"error": "Invalid or expired refresh token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        validated_data = serializer.validated_data
        access_token = validated_data.get("access")
        new_refresh_token = validated_data.get("refresh", refresh_token)
        if platform == "web":
            response = Response(
                {"message": "Token refreshed successfully"}, status=status.HTTP_200_OK
            )

            response.set_cookie(
                "access_token",
                access_token,
                max_age=5 * 60,
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
                domain=settings.COOKIE_DOMAIN,
            )
            response.set_cookie(
                "refresh_token",
                new_refresh_token,
                max_age=90 * 24 * 60 * 60,
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
                domain=settings.COOKIE_DOMAIN,
            )
        else:
            response = Response(
                {
                    "message": "Token refreshed successfully",
                    "access": access_token,
                    "refresh": new_refresh_token,
                },
                status=status.HTTP_200_OK,
            )
        return response


@USER_DELETE_SCHEMA
class UserDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user = request.user

        refresh_token = request.data.get("refresh")

        return clear_auth_session(
            refresh_token=refresh_token, request=request, user=user
        )
