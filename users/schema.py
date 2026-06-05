from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers

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

OTP_REQUEST_SCHEMA = extend_schema_view(
    post=extend_schema(
        tags=["Authentication"],
        summary="Request OTP",
        description="Sends a One-Time Password (OTP) to the provided email address for user verification. "
        "Validates if the email is already registered.",
        request=SignupOTPRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name="OTPRequestSuccess",
                    fields={
                        "message": serializers.CharField(
                            default="An OTP has been successfully sent to your email address."
                        )
                    },
                ),
                description="OTP sent successfully.",
            ),
            400: OpenApiResponse(
                response=inline_serializer(
                    name="OTPRequestError",
                    fields={
                        "error": serializers.CharField(
                            default="Failed to send the OTP. Please try again later. (Or email already exists)"
                        )
                    },
                ),
                description="Bad Request. Invalid email format, or email already registered.",
            ),
        },
    )
)


OTP_VERIFICATION_SCHEMA = extend_schema_view(
    post=extend_schema(
        tags=["Authentication"],
        summary="Verify OTP",
        description="Verifies the OTP sent to the user's email address. Ensures the OTP is valid and has not expired.",
        request=SignupOTPVerificationSerializer,
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name="OTPVerifySuccess",
                    fields={
                        "message": serializers.CharField(
                            default="OTP verified successfully."
                        )
                    },
                ),
                description="OTP successfully verified.",
            ),
            400: OpenApiResponse(
                response=inline_serializer(
                    name="OTPVerifyError",
                    fields={
                        "error": serializers.CharField(
                            default="Invalid or expired OTP."
                        )
                    },
                ),
                description="Bad Request. OTP is incorrect or has expired.",
            ),
        },
    )
)

GOOGLE_LOGIN_SCHEMA = extend_schema_view(
    post=extend_schema(
        tags=["Authentication"],
        summary="Google OAuth Login / Sign Up",
        description=(
            "Handles Google Authentication for Cashevide. This is a multi-step workflow for new users:\n\n"
            "1. **First Hit**: Frontend sends only `google_id_token`. If the user is new, backend returns **HTTP 200** with `status: prompt_referral`.\n"
            "2. **Second Hit**: Frontend captures referral code & username, then sends `google_id_token`, `referral_code_input`, and `username`. Backend completes registration and returns **HTTP 201**.\n\n"
            "For existing users, they are authenticated immediately on the first hit and receive tokens (HTTP 200)."
        ),
        request=GoogleLoginSerializer,
        responses={
            200: inline_serializer(
                name="GoogleLoginOrPromptResponse",
                fields={
                    # Scenario A: Prompting for referral code and username for new users
                    "status": serializers.CharField(
                        default="prompt_referral", required=False
                    ),
                    "email": serializers.EmailField(required=False),
                    "full_name": serializers.CharField(required=False),
                    "full_name": serializers.CharField(required=False),
                    # Scenario B: Existing user logs in successfully
                    "message": serializers.CharField(
                        default="login successful", required=False
                    ),
                    "user": UserDetailSerializer(required=False),
                    "access": serializers.CharField(
                        required=False, help_text="JWT Access Token (Mobile only)"
                    ),
                    "refresh": serializers.CharField(
                        required=False, help_text="JWT Refresh Token (Mobile only)"
                    ),
                },
            ),
            # 🔹 201 Created: New user successfully completes registration
            201: inline_serializer(
                name="GoogleSignupSuccessResponse",
                fields={
                    "message": serializers.CharField(default="Signup successful"),
                    "user": UserDetailSerializer(),
                    "access": serializers.CharField(
                        required=False, help_text="JWT Access Token (Mobile only)"
                    ),
                    "refresh": serializers.CharField(
                        required=False, help_text="JWT Refresh Token (Mobile only)"
                    ),
                },
            ),
            # 🔹 400 Bad Request: Invalid Google token or serializer validation errors
            400: inline_serializer(
                name="GoogleLoginErrorResponse",
                fields={
                    "error": serializers.CharField(
                        default="Invalid or expired Google token."
                    ),
                },
            ),
        },
    )
)

USER_SIGNUP_SCHEMA = extend_schema_view(
    post=extend_schema(
        tags=["Authentication"],
        summary="User Registration / Sign Up",
        description="Registers a new user in the system.",
        responses={
            201: inline_serializer(
                name="SignupResponse",
                fields={
                    "message": serializers.CharField(
                        default="User registered successfully!"
                    ),
                    "data": UserDetailSerializer(),
                },
            )
        },
    )
)


USER_DELETE_SCHEMA = extend_schema_view(
    delete=extend_schema(
        tags=["Authentication"],
        summary="Delete User Account",
        description="Permanently deletes the currently authenticated user's account and their profile. If the request is from a mobile platform, pass the refresh token in the request body.",
        request=inline_serializer(
            name="DeleteUserRequest",
            fields={
                "refresh": serializers.CharField(
                    required=False,
                    help_text="Provide refresh token for mobile platform",
                )
            },
        ),
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name="DeleteUserResponse",
                    fields={
                        "message": serializers.CharField(
                            default="Account successfully deleted."
                        )
                    },
                ),
                description="Account successfully deleted",
            )
        },
    )
)

USER_PROFILE_SCHEMA = extend_schema_view(
    get=extend_schema(
        tags=["Users"],
        summary="Get User Profile",
        description="Retrieves the profile information of the currently authenticated user.",
    ),
    patch=extend_schema(
        tags=["Users"],
        summary="Partial Update User Profile",
        description="Updates specific fields of the user's profile.",
        request={"multipart/form-data": UserProfileSerializer},
    ),
    put=extend_schema(
        tags=["Users"],
        summary="Update User Profile",
        description="Updates the entire profile of the user.",
        request={"multipart/form-data": UserProfileSerializer},
    ),
)

USER_BUSINESS_PROFILE_SCHEMA = extend_schema_view(
    get=extend_schema(
        tags=["Users"],
        summary="Get User Business Profile",
        description="Retrieves the business profile information of the currently authenticated user.",
    ),
    patch=extend_schema(
        tags=["Users"],
        summary="Partial Update Business Profile",
        description="Updates specific fields of the user's business profile.",
        request={"multipart/form-data": UserBusinessProfileSerializer},
    ),
    put=extend_schema(
        tags=["Users"],
        summary="Update User Business Profile",
        description="Updates the entire business profile of the user.",
        request={"multipart/form-data": UserBusinessProfileSerializer},
    ),
)

USER_CHECK_FIELD_SCHEMA = extend_schema_view(
    get=extend_schema(
        tags=["Users"],
        summary="Check Field Availability",
        description="Checks whether a specific field (like 'username' or 'email') is already taken in the database. \n\n"
        "Returns `is_available: true` if the value is not taken and can be used. "
        "Returns an error if the field is invalid or missing.",
        parameters=[
            OpenApiParameter(
                name="field",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="The name of the field to check. Allowed values: `username`, `email`.",
                required=True,
            ),
            OpenApiParameter(
                name="value",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="The value you want to check for availability.",
                required=True,
            ),
        ],
    )
)

PASSWORD_CHANGE_SCHEMA = extend_schema_view(
    post=extend_schema(
        tags=["Authentication"],
        summary="Change User Password",
        description="Allows an authenticated user to change their password securely. Requires the current password and the new password. Upon a successful password change, the user's refresh token is blacklisted, cookies are cleared, and they must log in again.",
        request=PasswordChangeSerializer,
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name="PasswordChangeSuccess",
                    fields={
                        "detail": serializers.CharField(
                            default="Password has been updated successfully. Please login again."
                        )
                    },
                ),
                description="Password successfully changed and user logged out from the current session.",
            ),
            400: OpenApiResponse(
                response=inline_serializer(
                    name="PasswordChangeError",
                    fields={
                        "old_password": serializers.ListField(
                            child=serializers.CharField(
                                default="Invalid current password."
                            ),
                            required=False,
                        ),
                        "new_password": serializers.ListField(
                            child=serializers.CharField(
                                default="This field is required."
                            ),
                            required=False,
                        ),
                    },
                ),
                description="Bad Request. Invalid current password or validation errors.",
            ),
            401: OpenApiResponse(
                description="Unauthorized. User must be authenticated to change password.",
            ),
        },
    )
)

USER_LOGIN_SCHEMA = extend_schema_view(
    post=extend_schema(
        tags=["Authentication"],
        summary="User Login (Multi-platform)",
        description="Authenticates the user using their credentials. \n\n"
        "**Token Delivery:**\n"
        "* If platform is `web`: JWT tokens are set securely as HttpOnly cookies.\n"
        "* If platform is `mobile` (default): JWT tokens are returned directly in the JSON response.",
        request=UserLoginSerializer,
    )
)

PASSWORD_RESET_OTP_REQUEST_SCHEMA = extend_schema_view(
    post=extend_schema(
        tags=["Authentication"],
        summary="Request Password Reset OTP",
        description="Sends a One-Time Password (OTP) to the user's email to initiate the password reset process. Fails if the email is not registered in the system.",
        request=PasswordResetOTPRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name="PasswordResetOTPRequestSuccess",
                    fields={
                        "message": serializers.CharField(
                            default="An OTP has been successfully sent to your email address."
                        )
                    },
                ),
                description="OTP sent successfully.",
            ),
            400: OpenApiResponse(
                response=inline_serializer(
                    name="PasswordResetOTPRequestError",
                    fields={
                        "email": serializers.ListField(
                            child=serializers.CharField(
                                default="No account found with this email address."
                            )
                        )
                    },
                ),
                description="Bad Request. Email not found or invalid format.",
            ),
        },
    )
)

PASSWORD_RESET_OTP_VERIFICATION_SCHEMA = extend_schema_view(
    post=extend_schema(
        tags=["Authentication"],
        summary="Verify Password Reset OTP",
        description="Verifies the OTP sent for password reset. Validates that the OTP is correct and hasn't expired.",
        request=PasswordResetVerificationSerializer,
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name="PasswordResetOTPVerifySuccess",
                    fields={
                        "message": serializers.CharField(
                            default="Email verification successful."
                        )
                    },
                ),
                description="OTP verified successfully.",
            ),
            400: OpenApiResponse(
                response=inline_serializer(
                    name="PasswordResetOTPVerifyError",
                    fields={
                        "otp": serializers.ListField(
                            child=serializers.CharField(
                                default="The OTP has expired or does not exist. Please request a new one."
                            )
                        )
                    },
                ),
                description="Bad Request. Invalid or expired OTP.",
            ),
        },
    )
)

PASSWORD_RESET_SCHEMA = extend_schema_view(
    post=extend_schema(
        tags=["Authentication"],
        summary="Reset User Password",
        description="Resets the user's password securely. Requires the email to be verified via the OTP verification endpoint first.",
        request=PasswordResetSerializer,
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name="PasswordResetSuccess",
                    fields={
                        "detail": serializers.CharField(
                            default="Password has been updated successfully."
                        )
                    },
                ),
                description="Password successfully reset.",
            ),
            400: OpenApiResponse(
                response=inline_serializer(
                    name="PasswordResetError",
                    fields={
                        "email": serializers.ListField(
                            child=serializers.CharField(
                                default="This email address has not been verified. Please verify it using an OTP first."
                            )
                        )
                    },
                ),
                description="Bad Request. Email not verified or validation errors.",
            ),
        },
    )
)

USER_LOGOUT_SCHEMA = extend_schema_view(
    post=extend_schema(
        tags=["Authentication"],
        summary="User Logout",
        description="Logs out the user by blacklisting their refresh token. If platform is `web`, the token is automatically taken from the cookies.",
        request=inline_serializer(
            name="LogoutRequest",
            fields={
                "refresh": serializers.CharField(
                    required=False,
                    help_text="Provide refresh token for mobile platform",
                )
            },
        ),
        responses={200: dict},
    )
)

TOKEN_REFRESH_SCHEMA = extend_schema_view(
    post=extend_schema(
        tags=["Authentication"],
        summary="Refresh Access Token",
        description="Generates a new access token using a valid refresh token. Platform defaults to `mobile`.",
        request=inline_serializer(
            name="TokenRefreshRequest",
            fields={
                "refresh": serializers.CharField(required=False),
                "platform": serializers.ChoiceField(
                    choices=["web", "mobile"], required=False, default="mobile"
                ),
            },
        ),
    )
)
