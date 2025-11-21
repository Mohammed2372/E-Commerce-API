from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from django.contrib.auth.models import User


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
