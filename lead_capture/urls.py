from django.urls import path

from .views import AnalyticsEventBatchView, AnalyticsEventView, AvailabilityView, ConsentView, LeadSubmissionView, PublicIndustriesView, PublicIntegrationsView, PublicScenariosView, RoiCalculationView, LocalizationConfigView, LocalizationCountryView, LocalizationPreferenceView, LocalizationMessagesView


urlpatterns = [
    path("leads", LeadSubmissionView.as_view(), name="v1-leads"),
    path("demo-requests", LeadSubmissionView.as_view(), name="v1-demo-requests"),
    path("pricing-requests", LeadSubmissionView.as_view(), name="v1-pricing-requests"),
    path("contact-requests", LeadSubmissionView.as_view(), name="v1-contact-requests"),
    path("analytics/events", AnalyticsEventView.as_view(), name="v1-analytics-events"),
    path("analytics/events/batch", AnalyticsEventBatchView.as_view(), name="v1-analytics-events-batch"),
    path("public/industries", PublicIndustriesView.as_view(), name="v1-public-industries"),
    path("public/industries/<slug:industry>", PublicIndustriesView.as_view(), name="v1-public-industry"),
    path("public/availability", AvailabilityView.as_view(), name="v1-public-availability"),
    path("public/industry-config/<slug:industry>", PublicIndustriesView.as_view(), name="v1-public-industry-config"),
    path("public/integrations", PublicIntegrationsView.as_view(), name="v1-public-integrations"),
    path("public/demo-scenarios/<slug:industry>", PublicScenariosView.as_view(), name="v1-public-scenarios"),
    path("consent", ConsentView.as_view(), name="v1-consent"),
    path("roi-calculations", RoiCalculationView.as_view(), name="v1-roi"),
    path("localization/config", LocalizationConfigView.as_view(), name="v1-localization-config"),
    path("localization/country", LocalizationCountryView.as_view(), name="v1-localization-country"),
    path("localization/preference", LocalizationPreferenceView.as_view(), name="v1-localization-preference"),
    path("localization/messages/<slug:locale>", LocalizationMessagesView.as_view(), name="v1-localization-messages"),
]
