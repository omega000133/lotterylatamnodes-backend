from rest_framework_simplejwt.authentication import JWTAuthentication


class AsppiWebToken(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        request.login_date = validated_token.get("login_date")
        return self.get_user(validated_token), validated_token