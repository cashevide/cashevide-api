from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User, UserSubscription

from .models import Client


class ClientTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="clientadmin@cashevide.com",
            username="clientadmin",
            password="CashevideStrong@2026",
        )
        self.client.force_authenticate(user=self.user)

        UserSubscription.objects.create(
            user=self.user, tier=UserSubscription.Tier.COMMUNITY
        )

        self.client.force_authenticate(user=self.user)
        self.url = reverse("client-list")

    def test_create_client_success(self):
        data = {
            "name": "Noufal K A",
            "email": "noufal@example.com",
            "phone": "+919876543210",
            "address": "Kodungallur, Kerala",
        }
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Noufal K A")

        self.assertIsNotNone(response.data["slug"])
        self.assertTrue(response.data["slug"].startswith("noufal-k-a"))

    def test_client_creation_limit_reached(self):
        for i in range(10):
            Client.objects.create(
                user=self.user, name=f"Test Client {i}", phone=f"+9190000000{i:02d}"
            )

        data = {
            "name": "Client 11",
            "phone": "+919000000011",
            "address": "Limit Test Address",
        }
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("You cannot create more than 10 clients", str(response.data))

    def test_list_clients(self):
        Client.objects.create(user=self.user, name="List Client 1", phone="1111111111")
        Client.objects.create(user=self.user, name="List Client 2", phone="2222222222")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)

    def test_update_client(self):
        client_obj = Client.objects.create(
            user=self.user, name="Old Name", phone="1234567890"
        )

        detail_url = reverse("client-detail", kwargs={"slug": client_obj.slug})

        data = {"name": "New Cashevide Client"}
        response = self.client.patch(detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "New Cashevide Client")

    def test_delete_client_is_soft_delete(self):
        client_obj = Client.objects.create(
            user=self.user, name="To Be Deleted", phone="9999999999"
        )
        detail_url = reverse("client-detail", kwargs={"slug": client_obj.slug})

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        client_obj.refresh_from_db()

        self.assertFalse(client_obj.is_active)
