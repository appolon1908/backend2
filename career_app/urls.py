from rest_framework.routers import DefaultRouter

from .views import CareerViewSet

router = DefaultRouter()

router.register(r'', CareerViewSet, basename='career')

urlpatterns = router.urls
