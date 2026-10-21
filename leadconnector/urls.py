from django.urls import path
from .views import webhook, LeadList, IntegrationStatus

urlpatterns = [
    path("webhook/",webhook,name="leadconnector-webhook"),
    path("leads/",LeadList.as_view(),name="leadconnector-leads"),
    path("status/",IntegrationStatus.as_view(),name="leadconnector-status"),
]
