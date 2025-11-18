from django_filters.rest_framework import FilterSet
from django_filters import NumberFilter

from .models import Product


class ProductFilter(FilterSet):
    min_price = NumberFilter(field_name="price", lookup_expr="gte")
    max_price = NumberFilter(field_name="price", lookup_expr="lte")

    class Meta:
        model = Product
        fields = ["name", "category", "min_price", "max_price"]
