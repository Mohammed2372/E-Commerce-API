from rest_framework import viewsets, filters, permissions, mixins, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.decorators import action


from .models import Product, Cart, CartItem
from .serializers import (
    ProductSerializer,
    ProductDetailSerializer,
    CartSerializer,
    CartItemSerializer,
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


class CartViewSet(
    mixins.ListModelMixin,  # Enables GET /cart/ to list all carts (if user has multiple)
    mixins.RetrieveModelMixin,  # GET /cart/ to retrieve the cart details
    mixins.DestroyModelMixin,  # DELETE /cart/ to clear the cart (optional: delete by ID)
    viewsets.GenericViewSet,  # Base class for custom actions
):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).order_by("-created_at")

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=["post"], serializer_class=CartItemSerializer)
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

        try:
            cart, created = Cart.objects.get_or_create(user=user)
            product = Product.objects.get(pk=product_id)

            cart_item, item_created = CartItem.objects.get_or_create(
                cart=cart, product=product, defaults={"quantity": quantity}
            )

            if not item_created:
                cart_item.quantity += quantity
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
            return Response({"error": "Product not found."}, status=404)
        except Exception as e:
            # NOTE: This is a general error catch, add more specific validation checks later
            return Response({"error": str(e)}, status=400)
