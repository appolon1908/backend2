import logging
from django.utils.timezone import now
from user_agents import parse

from auth_app.tasks import log_visitor_details



logger = logging.getLogger(__name__)

class VisitorTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        try:
            # Extract visitor information
            ip_address = self.get_client_ip(request)
            user_agent_string = request.META.get("HTTP_USER_AGENT", "")
            user_agent = parse(user_agent_string)
            page = request.build_absolute_uri()
            method = request.method

            # Prepare data for Celery task
            visitor_data = {
                "ip_address": ip_address,
                "page": page,
                "device": user_agent.device.family,
                "os": user_agent.os.family,
                "browser": user_agent.browser.family,
                "method": method,
                "visited_at": now().isoformat(),
            }
            
            # Send data to Celery task
            log_visitor_details.delay(visitor_data)

        except Exception as e:
            logger.error(f"Error tracking visitor: {e}")

        return response

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip