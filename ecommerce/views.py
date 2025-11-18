from rest_framework import viewsets, filters, permissions, mixins
from django_filters.rest_framework import DjangoFilterBackend


from .models import Product
from .serializers import ProductSerializer, ProductDetailSerializer, Cart, CartItem
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
