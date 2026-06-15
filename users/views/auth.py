from django.conf import settings
from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User
from users.schema import (
    GOOGLE_AUTH_SCHEMA,
    USER_LOGIN_SCHEMA,
    USER_LOGOUT_SCHEMA,
    USER_SIGNUP_SCHEMA,
)
from users.serializers.auth import (
    GoogleAuthSerializer,
    UserDetailSerializer,
    UserLoginSerializer,
)
from users.services import create_user_account
from users.utils import set_auth_cookies


@GOOGLE_AUTH_SCHEMA
class GoogleAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = GoogleAuthSerializer(data=request.data)

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
