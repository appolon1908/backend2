import uuid
from django.db import models
from django.contrib.auth import get_user_model



User = get_user_model()



def generate_id():
    return uuid.uuid4().hex



class Event(models.Model):

    EVENT_TYPE = (
        ('purchase', 'Purchase'),
        ('call', 'Call'),
        ('meeting', 'Meeting'),
        ('appointment', 'Appointment'),
        ('other', 'Other'),
    )
    id = models.UUIDField(default=generate_id, primary_key=True, unique=True, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE, default='meeting')
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, blank=True)
    employee = models.ForeignKey('employee.Employee', null=True, blank=True, on_delete=models.SET_NULL)
    customer = models.ForeignKey('customers.Customer', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.title
