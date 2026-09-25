from django.urls import path
from .internal_views import ControlledEventView, DeliveryView, ReconciliationView

urlpatterns = [
    path("odoo/leads", DeliveryView.as_view()), path("odoo/activities", ControlledEventView.as_view()),
    path("odoo/attribution", ControlledEventView.as_view()), path("odoo/delivery/retry", DeliveryView.as_view()),
    path("odoo/reconciliation/run", ReconciliationView.as_view()),
    path("odoo/delivery/<uuid:submission_id>", DeliveryView.as_view()),
    path("odoo/reconciliation/failures", ReconciliationView.as_view()),
    path("n8n/events", ControlledEventView.as_view()), path("notifications/dispatch", ControlledEventView.as_view()),
]
