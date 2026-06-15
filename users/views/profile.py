from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated

from users.models import UserBusinessProfile, UserProfile
from users.schema import (
    USER_BUSINESS_PROFILE_SCHEMA,
    USER_PROFILE_SCHEMA,
)
from users.serializers.profile import (
    UserBusinessProfileSerializer,
    UserProfileSerializer,
)


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
