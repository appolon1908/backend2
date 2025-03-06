from django.http import JsonResponse
# from .models import BlacklistedIP
from auth_app.models import BlacklistedIP

class BlockBlacklistedIPsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip_address = self.get_client_ip(request)
        if BlacklistedIP.objects.filter(ip_address=ip_address).exists():
            return JsonResponse({"error": "You are blocked from visiting this page."}, status=403)

        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip