from django.db import models

from uuid import uuid4


def get_customer_id():
    return str(uuid4().hex)[:6].upper()


class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    customer_id = models.CharField(max_length=256, unique=True, default=get_customer_id)
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return self.first_name + " " + self.last_name
    
    