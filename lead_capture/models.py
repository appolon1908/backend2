import uuid

from django.db import models


class LeadSubmission(models.Model):
    class DeliveryStatus(models.TextChoices):
        QUEUED = "queued", "Queued"
        DELIVERED = "delivered", "Delivered"
        FAILED = "failed", "Failed"
        DEAD_LETTER = "dead_letter", "Dead letter"

    request_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    idempotency_key_hash = models.CharField(max_length=64, unique=True, editable=False)
    duplicate_fingerprint = models.CharField(max_length=64, db_index=True, editable=False)
    full_name = models.CharField(max_length=160)
    business_name = models.CharField(max_length=200)
    work_email = models.EmailField()
    phone_number = models.CharField(max_length=32)
    country = models.CharField(max_length=80)
    preferred_language = models.CharField(max_length=40)
    content_locale = models.CharField(max_length=8, default="en")
    country_code = models.CharField(max_length=2, blank=True)
    locale_source = models.CharField(max_length=24, default="fallback")
    translation_version = models.CharField(max_length=40, blank=True)
    industry = models.CharField(max_length=100)
    industry_code = models.CharField(max_length=40, blank=True, db_index=True)
    campaign_code = models.CharField(max_length=64, blank=True, db_index=True)
    team_code = models.CharField(max_length=64, blank=True)
    source_code = models.CharField(max_length=64, blank=True)
    medium_code = models.CharField(max_length=64, blank=True)
    assignment_queue = models.CharField(max_length=64, blank=True)
    solution_code = models.CharField(max_length=100, blank=True)
    employee_count = models.CharField(max_length=40)
    monthly_call_volume = models.CharField(max_length=40)
    product_interest = models.CharField(max_length=120)
    preferred_demo_date = models.DateField(null=True, blank=True)
    preferred_demo_time = models.TimeField(null=True, blank=True)
    message = models.TextField(blank=True)
    consent = models.BooleanField()
    attribution = models.JSONField(default=dict)
    landing_page_url = models.URLField(max_length=1000, blank=True)
    referrer = models.URLField(max_length=1000, blank=True)
    cta_clicked = models.CharField(max_length=120, blank=True)
    anonymous_session_id = models.CharField(max_length=64, db_index=True)
    lead_score = models.PositiveSmallIntegerField(default=0)
    lead_classification = models.CharField(max_length=32, blank=True, db_index=True)
    score_reasons = models.JSONField(default=list)
    follow_up_sla_minutes = models.PositiveIntegerField(default=1440)
    delivery_status = models.CharField(max_length=16, choices=DeliveryStatus.choices, default=DeliveryStatus.QUEUED, db_index=True)
    delivery_attempts = models.PositiveSmallIntegerField(default=0)
    delivery_reference = models.CharField(max_length=128, blank=True)
    delivery_error_code = models.CharField(max_length=64, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.business_name} — {self.product_interest}"


class AnalyticsEvent(models.Model):
    event_name = models.CharField(max_length=64, db_index=True)
    anonymous_session_id = models.CharField(max_length=64, db_index=True)
    occurred_at = models.DateTimeField()
    page_path = models.CharField(max_length=300)
    cta_name = models.CharField(max_length=120, blank=True)
    section = models.CharField(max_length=120, blank=True)
    industry = models.CharField(max_length=40, blank=True, db_index=True)
    solution = models.CharField(max_length=100, blank=True)
    cta_position = models.CharField(max_length=100, blank=True)
    attribution = models.JSONField(default=dict)
    device_category = models.CharField(max_length=20)
    language = models.CharField(max_length=16)
    consent_state = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_name} — {self.anonymous_session_id}"
