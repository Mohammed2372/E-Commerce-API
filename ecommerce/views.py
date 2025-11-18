from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend


from .models import Product
from .serializers import ProductSerializer
from .permissions import IsAdminOrReadOnly
from .filters import ProductFilter


# Create your views here.
## Product with *ModelViewSet*
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    ordering_fields = ["price", "created_at"]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = ProductFilter
    search_fields = ["name", "description"]

