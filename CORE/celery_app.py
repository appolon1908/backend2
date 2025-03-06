import os

from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CORE.settings')

app = Celery('CORE')


app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
    

app.conf.beat_schedule = {
    'publish_scheduled_blogs': {
        'task': 'blog_app.tasks.publish_scheduled_blogs',
        'schedule': crontab(minute=0, hour='*'),
    },
    'send_event_reminders': {
        'task': 'calendar_app.tasks.send_event_reminders',
        'schedule': crontab(minute=0, hour=0),
    }
}