from datetime import date
from celery import shared_task
from .models import Blog
from datetime import datetime



        
@shared_task
def publish_scheduled_blogs():
    """
    Publishes all blogs that are scheduled to be published now.

    This function retrieves all blogs with a status of 'SCHEDULED' and a scheduled_date
    equal to the current datetime. It then updates their status to 'PUBLISHED' and sets the 
    published_at field to the current datetime, saving these changes to the database.

    Returns:
        None
    """
    now = datetime.now()
    today = date.today()
    current_hour = now.hour
    scheduled_blogs = Blog.objects.filter(status=Blog.SCHEDULED, scheduled_date__date=today, scheduled_date__hour=current_hour)
    for blog in scheduled_blogs:
        blog.status = Blog.PUBLISHED
        blog.published_at = now
        blog.save()