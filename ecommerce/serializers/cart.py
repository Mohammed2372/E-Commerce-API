from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from .product import ProductSerializer
from ..models import Product, Cart, CartItem


class CartItemSerializer(ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product", write_only=True
    )
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = [
            # "id",
            "product",
            "product_id",
            "quantity",
            "subtotal",
        ]
        extra_kwargs = {"cart": {"read_only": True}}


class CartSerializer(ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "user", "status", "items", "total_price", "created_at"]
