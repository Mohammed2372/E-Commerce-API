from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from ..serializers import UserRegistrationSerializer, UserDetailSerializer


## helper function for tokens
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


# --- Registration --- #
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer


# --- Login Authentication --- #
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request) -> Response:
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)

        if user is not None:
            tokens = get_tokens_for_user(user)
            response = Response(
                {"message": "Login successful"}, status=status.HTTP_200_OK
            )

            # Set Access Token Cookie
            response.set_cookie(
                key="access_token",
                value=tokens["access"],
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
                max_age=3600,  # 1 hour
            )

            # Set Refresh Token Cookie
            response.set_cookie(
                key="refresh_token",
                value=tokens["refresh"],
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
                max_age=604800,  # 7 days
            )
            return response

        return Response(
            {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
        )


class LogoutView(APIView):
    def post(self, request) -> Response:
        response = Response({"message": "Logout successful"})
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response


class CookieTokenRefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # 1. Get the Refresh Token from the cookie
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response(
                {"error": "No refresh token found"}, status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            refresh = RefreshToken(refresh_token)

            new_access_token = str(refresh.access_token)

            response = Response(
                {"message": "Access token refreshed"}, status=status.HTTP_200_OK
            )

            # 4. Set the NEW Access Token in the cookie
            response.set_cookie(
                key="access_token",
                value=new_access_token,
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
                max_age=3600,  # 1 hour
            )

            return response

        except (TokenError, InvalidToken):
            return Response(
                {"error": "Invalid or expired refresh token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )


# --- User --- #
class UserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)
