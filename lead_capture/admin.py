from django.contrib import admin

from .models import AnalyticsEvent, LeadSubmission
from .tasks import deliver_lead


@admin.register(LeadSubmission)
class LeadSubmissionAdmin(admin.ModelAdmin):
    list_display = ("business_name", "full_name", "work_email", "product_interest", "delivery_status", "created_at")
    list_filter = ("delivery_status", "product_interest", "industry", "created_at")
    search_fields = ("business_name", "full_name", "work_email", "request_id")
    readonly_fields = ("request_id", "idempotency_key_hash", "duplicate_fingerprint", "delivery_attempts", "delivery_reference", "delivery_error_code", "delivered_at", "created_at", "updated_at")
    actions = ("retry_delivery",)

    @admin.action(description="Retry selected lead deliveries")
    def retry_delivery(self, request, queryset):
        for lead in queryset:
            deliver_lead.delay(lead.pk)
        self.message_user(request, f"Queued {queryset.count()} lead deliveries.")


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ("event_name", "anonymous_session_id", "page_path", "created_at")
    list_filter = ("event_name", "device_category", "consent_state", "created_at")
    readonly_fields = [field.name for field in AnalyticsEvent._meta.fields]
