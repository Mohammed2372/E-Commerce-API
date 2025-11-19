from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from .models import Product, Category, Cart, CartItem


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
            "in_stock",
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


# --- Cart Serializers ---
class CartItemSerializer(ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product", write_only=True
    )
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_id", "quantity", "subtotal"]
        extra_kwargs = {"cart": {"read_only": True}}


class CartSerializer(ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "user", "status", "items", "total_price", "created_at"]
