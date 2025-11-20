from django.urls import path, include
from rest_framework.routers import DefaultRouter


from .views import (
    ProductViewSet,
    CartViewSet,
    CartItemViewSet,
    RegisterView,
    LoginView,
    LogoutView,
    UserView,
    CookieTokenRefreshView,
)


app_name = "products"
router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")
router.register(r"cart", CartViewSet, basename="cart")
router.register(r"cart_items", CartItemViewSet, basename="cart_items")

urlpatterns = [
    # Main API routes
    path("", include(router.urls)),
    # Authentication Endpoints
    path("user/", UserView.as_view(), name="user"),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),
    path("api-auth/", include("rest_framework.urls")),
]
