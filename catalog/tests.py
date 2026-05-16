from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Product
from users.models import User, UserSubscription


class ProductTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="catalogadmin@cashevide.com",
            username="catalogadmin",
            password="CashevideStrong@2026",
        )

        UserSubscription.objects.create(
            user=self.user, tier=UserSubscription.Tier.COMMUNITY
        )

        self.client.force_authenticate(user=self.user)
        self.url = reverse("product-list")

    def test_create_product_success(self):
        data = {
            "title": "Cashevide Pro Service",
            "description": "Professional consulting service for freelancers",
            "unit_price": "999.50",
        }
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Cashevide Pro Service")
        self.assertEqual(response.data["unit_price"], "999.50")

        self.assertIsNotNone(response.data["slug"])
        self.assertTrue(response.data["slug"].startswith("cashevide-pro-service"))

    def test_product_creation_limit_reached(self):
        for i in range(10):
            Product.objects.create(
                user=self.user, title=f"Test Product {i}", unit_price="100.00"
            )

        data = {
            "title": "Product 11",
            "description": "Limit test description",
            "unit_price": "200.00",
        }
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("You cannot create more than 10 products", str(response.data))

    def test_list_products(self):
        Product.objects.create(user=self.user, title="Product A", unit_price="10.00")
        Product.objects.create(user=self.user, title="Product B", unit_price="20.00")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_update_product(self):
        product_obj = Product.objects.create(
            user=self.user, title="Old Title", unit_price="50.00"
        )
        detail_url = reverse("product-detail", kwargs={"slug": product_obj.slug})

        data = {"title": "Updated Title"}
        response = self.client.patch(detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated Title")

    def test_delete_product_is_soft_delete(self):
        product_obj = Product.objects.create(
            user=self.user, title="To Be Deleted", unit_price="99.00"
        )
        detail_url = reverse("product-detail", kwargs={"slug": product_obj.slug})

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        product_obj.refresh_from_db()
        self.assertFalse(product_obj.is_active)
