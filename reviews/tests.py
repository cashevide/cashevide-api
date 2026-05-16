from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User

from .models import Review, ReviewedClient, Tag
from .utils import hash_phone_number


class ReviewedClientTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="clientcreator@cashevide.com",
            username="clientcreator",
            password="CashevideStrong@2026",
        )
        self.client.force_authenticate(user=self.user)

        self.url = reverse("reviewedclient-list")

    def test_create_reviewed_client_success(self):
        plain_number = "+918888888888"
        data = {"phone_number": "+918888888888"}
        response = self.client.post(self.url, data)

        expected_hash = hash_phone_number(plain_number)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["phone_number"], expected_hash)

    def test_list_reviewed_clients_forbidden_for_normal_user(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_reviewed_clients_success_for_superuser(self):
        superuser = User.objects.create_superuser(
            email="admin@cashevide.com",
            username="admin",
            password="CashevideStrong@2026",
        )
        self.client.force_authenticate(user=superuser)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ClientLookupTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="reviewer@cashevide.com",
            username="reviewer",
            password="CashevideStrong@2026",
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("client_lookup")

        self.test_phone = "+919876543210"
        self.reviewed_client = ReviewedClient.objects.create(
            phone_number=self.test_phone
        )

    def test_lookup_existing_client(self):
        data = {"phone_number": self.test_phone}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Client found successfully")
        self.assertIn("client_id", response.data)

    def test_lookup_non_existing_client(self):
        data = {"phone_number": "+919999999999"}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "client not found")

    def test_lookup_invalid_phone_number(self):
        data = {"phone_number": "12345"}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TagTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="taguser@cashevide.com",
            username="taguser",
            password="CashevideStrong@2026",
        )

        self.superuser = User.objects.create_superuser(
            email="tagadmin@cashevide.com",
            username="tagadmin",
            password="CashevideStrong@2026",
        )

        self.tag = Tag.objects.create(
            name="Good Communication", category="POSITIVE", group="communication"
        )

        self.url = reverse("tag-list")

    def test_list_tags_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_tag_forbidden_for_normal_user(self):
        self.client.force_authenticate(user=self.user)
        data = {"name": "Fast Payer", "category": "POSITIVE", "group": "payment"}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_tag_success_for_superuser(self):
        self.client.force_authenticate(user=self.superuser)
        data = {"name": "Fast Payer", "category": "POSITIVE", "group": "payment"}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Fast Payer")

    def test_update_tag_success_for_superuser(self):
        self.client.force_authenticate(user=self.superuser)

        detail_url = reverse("tag-detail", kwargs={"pk": self.tag.pk})

        data = {"name": "Excellent Communication"}
        response = self.client.patch(detail_url, data)

        detail_url = reverse("tag-detail", kwargs={"pk": self.tag.pk})

        data = {"name": "Excellent Communication"}
        response = self.client.patch(detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Excellent Communication")

    def test_delete_tag_success_for_superuser(self):
        self.client.force_authenticate(user=self.superuser)
        detail_url = reverse("tag-detail", kwargs={"pk": self.tag.pk})

        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class ReviewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="reviewer1@cashevide.com",
            username="reviewer1",
            password="CashevideStrong@2026",
        )
        self.client.force_authenticate(user=self.user)

        self.reviewed_client = ReviewedClient.objects.create(
            phone_number="+917777777777"
        )

        self.tag_good_pay = Tag.objects.create(
            name="Good Payer", category="POSITIVE", group="payment"
        )
        self.tag_fast_reply = Tag.objects.create(
            name="Fast Reply", category="POSITIVE", group="communication"
        )
        self.tag_late_pay = Tag.objects.create(
            name="Late Payer", category="NEGATIVE", group="payment"
        )

        self.url = reverse(
            "client_review", kwargs={"client_id": self.reviewed_client.id}
        )

    def test_create_review_success(self):
        data = {"ratings": 5, "tags": [self.tag_good_pay.id, self.tag_fast_reply.id]}  # type:ignore
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["ratings"], 5)

    def test_create_review_duplicate_fails(self):
        review = Review.objects.create(
            author=self.user, client=self.reviewed_client, ratings=4
        )
        review.tags.add(self.tag_good_pay)

        data = {"ratings": 3, "tags": [self.tag_fast_reply.id]}  # type:ignore
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("You have already reviewed this client!", str(response.data))

    def test_create_review_conflicting_tags_fails(self):
        data = {"ratings": 3, "tags": [self.tag_good_pay.id, self.tag_late_pay.id]}  # type:ignore
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("conflicting tags", str(response.data))

    def test_list_client_reviews(self):
        Review.objects.create(author=self.user, client=self.reviewed_client, ratings=4)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_review_summary(self):

        review1 = Review.objects.create(
            author=self.user, client=self.reviewed_client, ratings=5
        )
        review1.tags.add(self.tag_good_pay)

        user2 = User.objects.create_user(
            email="user2@cashevide.com", username="user2", password="pwd"
        )
        _ = Review.objects.create(author=user2, client=self.reviewed_client, ratings=3)

        summary_url = reverse(
            "client_review_summary", kwargs={"client_id": self.reviewed_client.id}
        )

        response = self.client.get(summary_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["total_reviews"], 2)

        self.assertEqual(response.data["average_rating"], 4.0)

        self.assertEqual(response.data["rating_distribution"][5], 1)
        self.assertEqual(response.data["rating_distribution"][3], 1)

    def test_list_excludes_inactive_reviews(self):
        Review.objects.create(
            author=self.user, client=self.reviewed_client, ratings=4, is_active=False
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_superuser_can_see_inactive_reviews(self):
        self.user.is_superuser = True
        self.user.save()

        Review.objects.create(
            author=self.user,
            client=self.reviewed_client,
            ratings=4,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)


class UserReviewTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            email="myreview_user@cashevide.com",
            username="myreview_user",
            password="pwd",
        )
        self.client.force_authenticate(user=self.user1)

        self.user2 = User.objects.create_user(
            email="other_user@cashevide.com", username="other_user", password="pwd"
        )

        self.reviewed_client = ReviewedClient.objects.create(
            phone_number="+918888888888"
        )

        self.review1 = Review.objects.create(
            author=self.user1, client=self.reviewed_client, ratings=4
        )

        self.review2 = Review.objects.create(
            author=self.user2, client=self.reviewed_client, ratings=2
        )

        self.list_url = reverse("my_reviews-list")
        self.detail_url = reverse("my_reviews-detail", kwargs={"pk": self.review1.pk})

    def test_list_only_own_reviews(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.review1.id)  # type:ignore

    def test_create_review_fails_with_custom_message(self):
        data = {"ratings": 5}
        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"], "Use client endpoint to create reviews."
        )

    def test_update_own_review(self):
        data = {"ratings": 5}
        response = self.client.patch(self.detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ratings"], 5)

    def test_delete_own_review(self):
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.filter(pk=self.review1.pk).exists())
