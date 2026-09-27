import re

from rest_framework import serializers

from .models import AnalyticsEvent, LeadSubmission
from .routing import CTA_SLA_MINUTES, resolve_industry, resolve_solution, score_lead


EVENT_NAMES = {
    "page_view", "section_view", "cta_click", "phone_demo_click",
    "audio_demo_started", "audio_demo_completed", "industry_selected",
    "calculator_started", "calculator_completed", "pricing_viewed",
    "lead_form_opened", "lead_form_started", "lead_form_validation_failed",
    "lead_submitted", "lead_delivery_succeeded", "lead_delivery_failed", "demo_requested",
    "industry_page_view", "cta_impression", "sticky_cta_viewed", "sticky_cta_clicked",
    "demo_viewed", "demo_started", "demo_paused", "demo_completed", "scenario_selected",
    "transcript_opened", "form_opened", "form_started", "form_abandoned", "form_submitted",
    "submission_accepted", "lead_delivery_started", "odoo_lead_created", "pricing_requested",
    "consultation_requested",
    "phone_click", "phone_call_connected", "workflow_viewed", "integration_viewed",
    "form_field_error", "thank_you_viewed", "return_visit", "qualified_lead",
    "opportunity_created", "opportunity_won", "opportunity_lost", "odoo_activity_created",
    "demo_scheduled",
    "industry_directory_viewed", "industry_search_used", "industry_filter_selected",
    "industry_card_viewed", "industry_card_clicked", "related_industry_clicked",
    "solution_selected", "qualifying_question_answered", "industry_demo_started",
    "industry_demo_completed", "industry_roi_completed", "industry_lead_submitted",
}


class LeadSubmissionSerializer(serializers.ModelSerializer):
    honeypot = serializers.CharField(required=False, allow_blank=True, write_only=True)
    solution = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = LeadSubmission
        fields = [
            "full_name", "business_name", "work_email", "phone_number", "country",
            "preferred_language", "industry", "employee_count", "monthly_call_volume",
            "product_interest", "preferred_demo_date", "preferred_demo_time", "message",
            "consent", "attribution", "landing_page_url", "referrer", "cta_clicked",
            "anonymous_session_id", "honeypot",
            "solution",
            "content_locale", "country_code", "locale_source", "translation_version",
        ]

    def validate_preferred_language(self, value):
        legacy = {"English": "en", "Spanish": "es", "French": "fr"}
        value = legacy.get(value, value)
        if value not in {"en", "es", "fr"}:
            raise serializers.ValidationError("Select a supported language.")
        return value

    def validate_content_locale(self, value):
        if value not in {"en", "es", "fr"}:
            raise serializers.ValidationError("Select a supported content locale.")
        return value

    def validate_locale_source(self, value):
        if value not in {"user_selection", "url", "browser", "country_suggestion", "fallback"}:
            raise serializers.ValidationError("Invalid locale source.")
        return value

    def validate_country_code(self, value):
        value = value.upper().strip()
        if value and not re.fullmatch(r"[A-Z]{2}", value):
            raise serializers.ValidationError("Invalid country code.")
        return value

    def validate_phone_number(self, value):
        normalized = re.sub(r"[^0-9+]", "", value)
        if normalized.startswith("00"):
            normalized = f"+{normalized[2:]}"
        if not re.fullmatch(r"\+?[0-9]{7,15}", normalized):
            raise serializers.ValidationError("Enter a valid telephone number.")
        return normalized

    def validate_consent(self, value):
        if not value:
            raise serializers.ValidationError("Consent is required.")
        return value

    def validate_honeypot(self, value):
        if value:
            raise serializers.ValidationError("Invalid submission.")
        return value

    def validate_industry(self, value):
        try:
            resolve_industry(value)
        except ValueError:
            raise serializers.ValidationError("Select a supported industry.")
        return value

    def create(self, validated_data):
        validated_data.pop("honeypot", None)
        requested_solution = validated_data.pop("solution", "")
        code, route = resolve_industry(validated_data["industry"])
        validated_data["industry_code"] = code
        validated_data["campaign_code"] = route["campaign"]
        validated_data["team_code"] = route["team_code"]
        validated_data["source_code"] = route["source_code"]
        validated_data["medium_code"] = route["medium_code"]
        validated_data["assignment_queue"] = route["queue_code"]
        validated_data["solution_code"] = resolve_solution(code, requested_solution or validated_data["product_interest"])
        score, classification, reasons = score_lead(validated_data)
        validated_data.update(lead_score=score, lead_classification=classification, score_reasons=reasons,
                              follow_up_sla_minutes=CTA_SLA_MINUTES.get(validated_data.get("cta_clicked"), 1440))
        return super().create(validated_data)


class AnalyticsEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsEvent
        fields = [
            "event_name", "anonymous_session_id", "occurred_at", "page_path", "cta_name",
            "section", "attribution", "device_category", "language", "consent_state",
            "industry", "solution", "cta_position",
        ]

    def validate_event_name(self, value):
        if value not in EVENT_NAMES:
            raise serializers.ValidationError("Unsupported event name.")
        return value

    def validate_attribution(self, value):
        allowed = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "gclid", "fbclid"}
        return {key: str(item)[:300] for key, item in value.items() if key in allowed}
