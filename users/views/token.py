import logging

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView

from users.schema import (
    TOKEN_REFRESH_SCHEMA,
)

logger = logging.getLogger(__name__)


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
