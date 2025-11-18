from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ProductViewSet, CartViewSet

app_name = "products"
router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")
router.register(r"cart", CartViewSet, basename="cart")

urlpatterns = [
    path("", include(router.urls)),
]
