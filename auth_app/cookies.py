from django.conf import settings
from django.middleware.csrf import get_token

def set_auth_cookies(response, request, *, access, refresh):
    response.set_cookie(settings.AUTH_ACCESS_COOKIE, access,
        max_age=settings.AUTH_ACCESS_COOKIE_MAX_AGE, httponly=True,
        secure=settings.AUTH_COOKIE_SECURE, samesite=settings.AUTH_COOKIE_SAMESITE, path="/")
    response.set_cookie(settings.AUTH_REFRESH_COOKIE, refresh,
        max_age=settings.AUTH_REFRESH_COOKIE_MAX_AGE, httponly=True,
        secure=settings.AUTH_COOKIE_SECURE, samesite=settings.AUTH_COOKIE_SAMESITE, path="/api/auth/")
    get_token(request)
    return response

def clear_auth_cookies(response):
    response.delete_cookie(settings.AUTH_ACCESS_COOKIE, path="/", samesite=settings.AUTH_COOKIE_SAMESITE)
    response.delete_cookie(settings.AUTH_REFRESH_COOKIE, path="/api/auth/", samesite=settings.AUTH_COOKIE_SAMESITE)
    return response
