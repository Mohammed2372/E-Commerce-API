from rest_framework_simplejwt.authentication import JWTAuthentication


# Custom authentication class to extract JWT token from cookies
class CookiesJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # check standard header first
        header = self.get_header(request)
        if header is not None:
            raw_token = self.get_raw_token(header)
        else:
            # if no header, check HttpOnly cookie
            raw_token = request.COOKIES.get("access_token")

        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except Exception:
            return None
