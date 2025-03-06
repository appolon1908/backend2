from django.db import models
import uuid



def generate_id():
    return uuid.uuid4().hex


def generate_ref():
    return uuid.uuid4().hex[:6]




class Transaction(models.Model):
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    id = models.UUIDField(default=generate_id, primary_key=True, unique=True, editable=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=256, unique=True)
    
    customer_id = models.CharField(max_length=256)
    customer_email = models.EmailField()
    client_secret = models.CharField(max_length=256, null=True, blank=True)
    currency = models.CharField(max_length=10, default='usd')
    status = models.CharField(max_length=50, default='pending')
    payment_method = models.CharField(max_length=50, null=True, blank=True)
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS, default='pending')
    meta_data = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.transaction_id
