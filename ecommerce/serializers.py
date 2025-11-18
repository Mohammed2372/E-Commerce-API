from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from .models import Product, Category


class ProductSerializer(ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field="name", many=True, read_only=True
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "category",
            "price",
            "in_stock",
            "created_at",
        ]


class ProductDetailSerializer(ModelSerializer):
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(), slug_field="name", many=True
    )

    class Meta:
        model = Product
        fields = "__all__"


class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"
