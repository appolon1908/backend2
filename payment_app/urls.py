from rest_framework.routers import DefaultRouter
from django.urls import path

from .views import PaymentViewSet
from .webhook_api import WebhookSubscriptionViewSet, deliveries, staging_receiver


router = DefaultRouter()

router.register(r'', PaymentViewSet, basename='payments')

urlpatterns = router.urls
webhook_router = DefaultRouter()
webhook_router.register(r'subscriptions', WebhookSubscriptionViewSet, basename='webhook-subscriptions')
urlpatterns += webhook_router.urls
urlpatterns += [path('deliveries/', deliveries), path('staging-receiver/', staging_receiver)]
