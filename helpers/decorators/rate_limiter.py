from time import time
from functools import wraps
from django.core.cache import cache
from django.http import JsonResponse
from rest_framework import status



def rate_limiter(key_func, rate=5, period=60):
    """
    A custom rate limiter decorator.

    Args:
        key_func (function): Function to determine the key (e.g., user or IP).
        rate (int): Maximum number of requests allowed.
        period (int): Time period in seconds.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Determine the key to use for rate limiting (e.g., user or IP)
            key = key_func(request)
            if not key:
                return JsonResponse({"error": "Could not determine rate limit key."}, status=400)

            # Current time in seconds
            now = int(time())

            # Cache key for tracking request timestamps
            cache_key = f"rate_limiter:{key}"

            # Retrieve request timestamps from the cache
            request_timestamps = cache.get(cache_key, [])

            # Filter out timestamps older than the period
            request_timestamps = [ts for ts in request_timestamps if ts > now - period]

            # Check if the rate limit is exceeded
            if len(request_timestamps) >= rate:
                return JsonResponse(
                    {"error": "Too many requests made. Try again later."}, 
                    status=status.HTTP_429_TOO_MANY_REQUESTS)

            # Add the current timestamp and save back to the cache
            request_timestamps.append(now)
            cache.set(cache_key, request_timestamps, timeout=period)

            # Proceed to the view
            return view_func(request, *args, **kwargs)

        return _wrapped_view
    return decorator




def get_client_ip(request):
    # Retrieve the client's IP address from the request
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


def user_or_ip_key(request):
    # Use user ID if authenticated, otherwise fallback to IP address
    if request.user.is_authenticated:
        return f"user:{request.user.id}"
    return f"ip:{get_client_ip(request)}"

