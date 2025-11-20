from django.shortcuts import get_object_or_404
from rest_framework import viewsets, filters, permissions, mixins, status, generics
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction  # for safe stock management
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.conf import settings
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken


from .models import Product, Cart, CartItem
from .serializers import (
    ProductSerializer,
    ProductDetailSerializer,
    CartSerializer,
    CartItemSerializer,
    UserRegistrationSerializer,
    UserDetailSerializer,
)
from .permissions import IsAdminOrReadOnly
from .filters import ProductFilter


# Create your views here.
## Product with *ModelViewSet*
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()

    # Dynamically switches serializers based on the request type (list or detail)
    def get_serializer_class(self):
        if self.action == "list":
            return ProductSerializer
        return ProductDetailSerializer

    permission_classes = [IsAdminOrReadOnly]
    ordering_fields = ["price", "created_at"]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = ProductFilter
    search_fields = ["name", "description"]


# --- Cart ViewSet ---
# Helper function to ensure we always interact with the user's current ACTIVE cart
def get_active_cart(user):
    # This ensures items go to the one shopping cart that is currently 'Active'
    # If no active cart exists, it creates one.
    cart, created = Cart.objects.get_or_create(user=user, status="Active")
    return cart


class CartViewSet(
    mixins.ListModelMixin,  # Enables GET /cart/ to list all carts (History)
    viewsets.GenericViewSet,  # Base class for custom actions
):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    # get user's carts
    def get_queryset(self):
        # Orders by status (so 'Active' cart is often last) and then by creation date.
        return Cart.objects.filter(user=self.request.user).order_by(
            "status", "-created_at"
        )

    # 1. RETRIEVE (GET /cart/my_cart/) - Retrieves the user's active cart
    @action(detail=False, methods=["get"], url_path="my_cart")
    def retrieve_active_cart(self, request):
        cart = get_active_cart(request.user)
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    # 2. ADD ITEM (POST /cart/add_item/) - Adds item to the active cart
    @action(
        detail=False,
        methods=["post"],
        serializer_class=CartItemSerializer,
        url_path="add_item",
        permission_classes=[permissions.IsAuthenticated],
    )
    def add_item(self, request):
        user = request.user
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity")

        try:
            quantity = int(quantity) if quantity is not None else 1
            if quantity < 1:
                return Response(
                    {"error": "Quantity must be at least 1."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except ValueError:
            return Response(
                {"error": "Quantity must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not product_id:
            return Response(
                {"error": "Product ID is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            try:
                cart = get_active_cart(user)
                if cart.status != "Active":
                    return Response(
                        {"error": "Cannot add items to a paid or closed cart."},
                        status=status.HTTP_403_FORBIDDEN,
                    )

                product = Product.objects.get(pk=product_id)

                cart_item, item_created = CartItem.objects.get_or_create(
                    cart=cart, product=product, defaults={"quantity": quantity}
                )

                quantity_to_add = quantity

                if product.in_stock < quantity:
                    return Response(
                        {
                            "error": f"Insufficient stock. Only {product.in_stock} units available."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # --- INVENTORY UPDATE ---
                product.in_stock -= quantity_to_add
                product.save()

                # --- CART UPDATE ---
                cart_item.quantity += quantity_to_add
                cart_item.save()

                cart.refresh_from_db()
                serializer = CartSerializer(cart)
                return Response(
                    serializer.data,
                    status=status.HTTP_200_OK
                    if not item_created
                    else status.HTTP_201_CREATED,
                )

            except Product.DoesNotExist:
                return Response(
                    {"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                return Response(
                    {"error": f"An unexpected error occurred: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

    # 3. CHECKOUT (POST /cart/checkout/) - Converts active cart to 'Paid'
    @action(detail=False, methods=["post"], url_path="checkout")
    def checkout(self, request):
        cart = get_active_cart(request.user)
        if cart.status != "Active":
            return Response(
                {
                    "error": f"Cart {cart.pk} is already marked as {cart.status} and cannot be checked out."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not cart.items.exists():
            return Response(
                {"error": "Cannot check out an empty cart."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart.status = "Paid"
        cart.save()

        serializer = CartSerializer(cart)
        return Response(
            {
                "message": f"Cart {cart.pk} successfully converted to Paid order. A new active cart will be implicitly created upon your next 'add_item' call.",
                "order": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    # 4. CLEAR (POST /cart/clear_active/) - Clears all items from the active cart
    @action(detail=False, methods=["post"])
    def clear_active_cart(self, request):
        cart = get_active_cart(request.user)

        if cart.status != "Active":
            return Response(
                {"error": "Cannot clear a cart that is already paid/closed."},
                status=status.HTTP_403_FORBIDDEN,
            )

        cart.delete()
        return Response(
            {"message": "Active cart has been completely deleted."},
            status=status.HTTP_204_NO_CONTENT,
        )


class CartItemViewSet(
    mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        active_cart = get_active_cart(self.request.user)
        return CartItem.objects.filter(cart=active_cart)

    def perform_update(self, serializer):
        cart_item = self.get_object()

        with transaction.atomic():
            if cart_item.cart.status != "Active":
                raise permissions.PermissionDenied(
                    "Cannot modify items in a closed or paid cart."
                )
            new_quantity = serializer.validated_data.get("quantity")
            old_quantity = cart_item.quantity

            if new_quantity is None:
                return serializer.save()

            quantity_difference = new_quantity - old_quantity

            # check stock for the requested change
            if quantity_difference > 0:
                product = cart_item.product
                if product.in_stock < quantity_difference:
                    raise permissions.PermissionDenied(
                        f"Insufficient stock to increase quantity. Only {product.in_stock} units available."
                    )

                # Decrease stock
                product.in_stock -= quantity_difference
                product.save()
            elif quantity_difference < 0:
                # If quantity decreases, return stock
                product = cart_item.product
                product.in_stock -= (
                    quantity_difference  # Subtracting a negative returns stock
                )
                product.save()
        # save
        serializer.save()

    def perform_destroy(self, instance):
        with transaction.atomic():
            if instance.cart.status != "Active":
                raise permissions.PermissionDenied(
                    "Cannot delete items in a closed or paid cart."
                )

            # return stock to inventory
            product = instance.product
            product.in_stock += instance.quantity
            product.save()

            # delete cart
            instance.delete()


# --- Registration --- #
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer


# --- Login Authentication --- #
## helper function for tokens
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request) -> Response:
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)

        if user is not None:
            tokens = get_tokens_for_user(user)
            response = Response(
                {"message": "Login successful"}, status=status.HTTP_200_OK
            )

            # Set Access Token Cookie
            response.set_cookie(
                key="access_token",
                value=tokens["access"],
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
                max_age=300,  # 5 minutes
            )

            # Set Refresh Token Cookie
            response.set_cookie(
                key="refresh_token",
                value=tokens["refresh"],
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
                max_age=86400,  # 1 day
            )
            return response

        return Response(
            {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
        )


class LogoutView(APIView):
    def post(self, request) -> Response:
        response = Response({"message": "Logout successful"})
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response


# --- User --- #
class UserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        print("serializer is working: ", serializer.data)
        return Response(serializer.data)
