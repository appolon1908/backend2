from celery import shared_task
from .models import Visitor



@shared_task
def log_visitor_details(visitor_data):
    
    try:
        visitor = Visitor(
            ip_address=visitor_data.get("ip_address"),
            page=visitor_data.get("page"),
            device=visitor_data.get("device"),
            os=visitor_data.get("os"),
            browser=visitor_data.get("browser"),
            method = visitor_data.get("method"),
            visited_at=visitor_data.get("visited_at"),
        )
        visitor.save()
    except Exception as e:
        raise Exception(f"Failed to log visitor details: {e}")