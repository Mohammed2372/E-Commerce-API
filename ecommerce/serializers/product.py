from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from ..models import Product, Category


class ProductSerializer(ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field="name", many=True, read_only=True
    )

    class Meta:
        model = Product
        fields = [
            "name",
            "category",
            "price",
            # "in_stock",  # to not show how many are there when showing active cart
        ]


class ProductDetailSerializer(ModelSerializer):
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(), slug_field="name", many=True
    )

    class Meta:
        model = Product
        fields = fields = [
            "id",
            "name",
            "description",
            "category",
            "price",
            "in_stock",
            "created_at",
        ]


class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"
