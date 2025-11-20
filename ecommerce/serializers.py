from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from django.contrib.auth.models import User

from .models import Product, Category, Cart, CartItem


# --- Product Serializers --- #
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


# --- User Registration Serializer --- #
class UserRegistrationSerializer(ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        label="Confirm Password",
    )
    # username = serializers.CharField(required=True)
    # email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "password2"]

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "passwords do not match"})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email"),
            password=validated_data["password"],
        )

        return user


# --- User Detail --- #
class UserDetailSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]
