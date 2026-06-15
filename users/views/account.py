import logging

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User
from users.schema import (
    PASSWORD_CHANGE_SCHEMA,
    PASSWORD_RESET_SCHEMA,
    USER_CHECK_FIELD_SCHEMA,
    USER_DELETE_SCHEMA,
)
from users.serializers import (
    PasswordChangeSerializer,
    PasswordResetSerializer,
)
from users.utils import clear_auth_session

logger = logging.getLogger(__name__)


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


@USER_DELETE_SCHEMA
class UserDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user = request.user

        refresh_token = request.data.get("refresh")

        return clear_auth_session(
            refresh_token=refresh_token, request=request, user=user
        )
