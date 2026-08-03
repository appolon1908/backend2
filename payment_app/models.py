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


class StripeWebhookEvent(models.Model):
    """Durable Stripe event receipt used for idempotent webhook processing."""

    event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=120)
    payload_sha256 = models.CharField(max_length=64)
    status = models.CharField(max_length=24, default="received")
    attempts = models.PositiveSmallIntegerField(default=0)
    last_error = models.CharField(max_length=255, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["status", "received_at"])]


class WebhookSubscription(models.Model):
    owner = models.ForeignKey("auth_app.User", on_delete=models.CASCADE, related_name="webhook_subscriptions")
    url = models.URLField(max_length=1000)
    name = models.CharField(max_length=120)
    secret = models.CharField(max_length=255)
    events = models.JSONField(default=list)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class WebhookDelivery(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        DELIVERED = "delivered", "Delivered"
        FAILED = "failed", "Failed"
        RETRYING = "retrying", "Retrying"

    subscription = models.ForeignKey(WebhookSubscription, on_delete=models.CASCADE, related_name="deliveries")
    event_id = models.UUIDField(default=uuid.uuid4, unique=True)
    event_type = models.CharField(max_length=120)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.QUEUED)
    attempts = models.PositiveSmallIntegerField(default=0)
    response_code = models.PositiveSmallIntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    error = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
