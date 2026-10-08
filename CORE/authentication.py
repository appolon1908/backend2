from django.conf import settings
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header_result = super().authenticate(request)
        if header_result is not None:
            return header_result
        raw_token = request.COOKIES.get(settings.AUTH_ACCESS_COOKIE)
        if not raw_token:
            return None
        validated_token = self.get_validated_token(raw_token)
        if request.method not in {"GET", "HEAD", "OPTIONS", "TRACE"}:
            SessionAuthentication().enforce_csrf(request)
        return self.get_user(validated_token), validated_token
