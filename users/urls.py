from django.urls import path

from users.views.account import (
    CheckFieldExistsView,
    PasswordChangeView,
    PasswordResetView,
    UserDeleteView,
)
from users.views.auth import GoogleAuthView, LoginView, LogoutView, UserSignupView
from users.views.otp import (
    PasswordResetOTPRequestView,
    PasswordResetOTPVerificationView,
    SignupOTPRequestView,
    SignupOTPVerificationView,
)
from users.views.profile import UserBusinessProfileView, UserProfileView
from users.views.token import CustomTokenRefreshView

urlpatterns = [
    path("signup-request-otp/", SignupOTPRequestView.as_view(), name="signup_send_otp"),
    path(
        "signup-verify-otp/",
        SignupOTPVerificationView.as_view(),
        name="signup_verify_otp",
    ),
    path("signup/", UserSignupView.as_view(), name="user_signup"),
    path("profile/me/", UserProfileView.as_view(), name="user_profile"),
    path(
        "business-profile/me/",
        UserBusinessProfileView.as_view(),
        name="user_business_profile",
    ),
    path("profile/delete/", UserDeleteView.as_view(), name="user_delete"),
    path("check-user/", CheckFieldExistsView.as_view(), name="check_user"),
    path("login/", LoginView.as_view(), name="login"),
    path("google/", GoogleAuthView.as_view(), name="google_login"),
    path("token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("change-password/", PasswordChangeView.as_view(), name="change_password"),
    path(
        "password-reset-request-otp/",
        PasswordResetOTPRequestView.as_view(),
        name="password_reset_send_otp",
    ),
    path(
        "password-reset-verify-otp/",
        PasswordResetOTPVerificationView.as_view(),
        name="password_reset_verify_otp",
    ),
    path("reset-password/", PasswordResetView.as_view(), name="reset_password"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
