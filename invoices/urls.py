from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import InvoiceViewSet

router = DefaultRouter()

router.register(r"invoices", InvoiceViewSet)

urlpatterns = [path("", include(router.urls))]
