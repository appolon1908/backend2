from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.utils import timezone
from celery import shared_task
from .models import Event

from notification.service import EmailService



@shared_task
def send_event_reminders():
    now = timezone.now()
    reminder_time = now + timedelta(days=1)
    events = Event.objects.filter(
            start_time__date=reminder_time.date(),
            employee__isnull=False
            )

    for event in events:
        subject = f"Reminder: Upcoming Event '{event.title}'"
        recipient_list = [event.employee.email]
        # send_mail(subject, message, 'no-reply@calendarapp.com', recipient_list)
        EmailService.send_async(
            template="event_reminder.html",
            subject=subject,
            recipient_list=recipient_list,
            context={
                "username": event.employee.first_name,
                "event_title": event.title,
                "event_date": event.start_time    
            }
            )