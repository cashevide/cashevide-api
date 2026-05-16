from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, UserProfile


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class SignupTests(APITestCase):
    def test_signup_otp_request_success(self):
        url = reverse("signup_send_otp")
        data = {"email": "test@email.com"}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"],
            "An OTP has been successfully sent to your email address.",
        )

        otp_in_cache = cache.get("signup_otp_test@email.com")
        self.assertIsNotNone(otp_in_cache)

    def test_signup_otp_verify_success(self):
        test_email = "test@email.com"
        test_otp = "123456"

        cache.set(f"signup_otp_{test_email}", test_otp, timeout=300)

        url = reverse("signup_verify_otp")
        data = {"email": test_email, "otp": test_otp}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Email verification successful.")

        is_verified = cache.get(f"signup_verified_{test_email}")
        self.assertTrue(is_verified)

    def test_signup_success(self):
        verified_email = "test@email.com"

        cache.set(f"signup_verified_{verified_email}", True, timeout=900)

        referrer = User.objects.create_user(
            email="referrer@cashevide.com", username="referrer", password="pwd"
        )
        UserProfile.objects.create(
            user=referrer, full_name="Referrer", referral_code="NOUFAL"
        )

        url = reverse("user_signup")
        data = {
            "email": verified_email,
            "full_name": "Test",
            "password": "CashevideStrong@2026",
            "platform": "mobile",
            "referral_code_input": "NOUFAL",
            "username": "test",
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "Signup successful")

    def test_login_success(self):
        User.objects.create_user(
            email="loginuser@cashevide.com",
            username="loginuser",
            password="CashevideStrong@2026",
        )

        url = reverse("login")
        data = {
            "email": "loginuser@cashevide.com",
            "password": "CashevideStrong@2026",
            "platform": "mobile",
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "login successful")
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)


class UserProfileTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="profileuser@cashevide.com",
            username="profileuser",
            password="CashevideStrong@2026",
        )
        UserProfile.objects.create(
            user=self.user, full_name="Profile User", referral_code="PRO123"
        )
        self.client.force_authenticate(user=self.user)

        self.url = reverse("user_profile")

    def test_get_user_profile(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "profileuser@cashevide.com")
        self.assertEqual(response.data["full_name"], "Profile User")

    def test_update_user_profile(self):

        data = {"phone_number": "9876543210", "job_title": "Software Engineer"}

        response = self.client.patch(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["phone_number"], "9876543210")
        self.assertEqual(response.data["job_title"], "Software Engineer")

    def test_put_user_profile(self):
        data = {
            "full_name": "Noufal Full Update",
            "phone_number": "1112223334",
            "job_title": "Full Stack Developer",
        }

        response = self.client.put(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["full_name"], "Noufal Full Update")
        self.assertEqual(response.data["job_title"], "Full Stack Developer")


class UserBusinessProfileTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="businessuser@cashevide.com",
            username="businessuser",
            password="CashevideStrong@2026",
        )

        self.client.force_authenticate(user=self.user)

        self.url = reverse("user_buisness_profile")

    def test_get_business_profile(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["business_name"], "")

    def test_patch_business_profile(self):
        data = {"business_name": "Cashevide Tech"}
        response = self.client.patch(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["business_name"], "Cashevide Tech")

    def test_put_business_profile(self):
        data = {
            "business_name": "Cashevide Complete",
            "address": "Kodungallur, Kerala",
            "phone_number": "9998887776",
            "currency": "INR",
        }
        response = self.client.put(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["business_name"], "Cashevide Complete")
        self.assertEqual(response.data["currency"], "INR")


class UserDeleteTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="deleteuser@cashevide.com",
            username="deleteuser",
            password="CashevideStrong@2026",
        )
        self.client.force_authenticate(user=self.user)

        self.url = reverse("user_delete")

    def test_delete_user(self):
        self.assertTrue(User.objects.filter(email="deleteuser@cashevide.com").exists())

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(User.objects.filter(email="deleteuser@cashevide.com").exists())


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class PasswordResetTests(APITestCase):
    def setUp(self):
        self.email = "resetuser@cashevide.com"
        self.user = User.objects.create_user(
            email=self.email,
            username="resetuser",
            password="OldPassword@2026",
        )

    def test_password_reset_otp_request(self):
        url = reverse("password_reset_send_otp")
        data = {"email": self.email}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"],
            "An OTP has been successfully sent to your email address.",
        )

        otp_in_cache = cache.get(f"password_reset_otp_{self.email}")
        self.assertIsNotNone(otp_in_cache)

    def test_password_reset_otp_verify(self):
        test_otp = "654321"
        cache.set(f"password_reset_otp_{self.email}", test_otp, timeout=300)

        url = reverse("password_reset_verify_otp")
        data = {"email": self.email, "otp": test_otp}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Email verification successful.")

        is_verified = cache.get(f"password_reset_verified_{self.email}")
        self.assertTrue(is_verified)

    def test_password_reset_success(self):
        cache.set(f"password_reset_verified_{self.email}", True, timeout=900)

        url = reverse("reset_password")
        new_password = "CashevideNewStrong@2026"
        data = {"email": self.email, "new_password": new_password}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"], "Password has been updated successfully."
        )

        self.user.refresh_from_db()

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))


class CheckUserTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="existing@cashevide.com",
            username="existinguser",
            password="CashevideStrong@2026",
        )
        self.url = reverse("check-user")

    def test_check_existing_username(self):
        response = self.client.get(
            self.url, {"field": "username", "value": "existinguser"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_available"])

    def test_check_new_username(self):
        response = self.client.get(self.url, {"field": "username", "value": "newuser"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_available"])

    def test_check_existing_email(self):
        response = self.client.get(
            self.url, {"field": "email", "value": "existing@cashevide.com"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_available"])

    def test_check_new_email(self):
        response = self.client.get(
            self.url, {"field": "email", "value": "newemail@cashevide.com"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_available"])

    def test_check_invalid_field(self):
        response = self.client.get(self.url, {"field": "phone", "value": "9876543210"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ChangePasswordTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="changepwd@cashevide.com",
            username="changepwduser",
            password="OldPassword@2026",
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("change_password")

    def test_change_password_success(self):
        data = {
            "current_password": "OldPassword@2026",
            "new_password": "CashevideNewStrong@2026",
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("CashevideNewStrong@2026"))

    def test_change_password_wrong_current_password(self):
        data = {
            "current_password": "WrongPassword@2026",
            "new_password": "CashevideNewStrong@2026",
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TokenRefreshTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="refreshuser@cashevide.com",
            username="refreshuser",
            password="CashevideStrong@2026",
        )
        self.url = reverse("token_refresh")

        refresh = RefreshToken.for_user(self.user)
        self.refresh_token = str(refresh)

    def test_token_refresh_mobile_success(self):
        data = {"refresh": self.refresh_token, "platform": "mobile"}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Token refreshed successfully")
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_token_refresh_invalid_token(self):
        data = {"refresh": "this_is_a_fake_and_invalid_token", "platform": "mobile"}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error"], "Invalid or expired refresh token")


class LogoutTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="logoutuser@cashevide.com",
            username="logoutuser",
            password="CashevideStrong@2026",
        )
        self.url = reverse("logout")

        refresh = RefreshToken.for_user(self.user)
        self.refresh_token = str(refresh)

    def test_logout_success(self):
        data = {"refresh": self.refresh_token}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Successfully logged out")

    def test_logout_no_token(self):
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Refresh token is required to logout")
