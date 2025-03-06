from rest_framework.routers import DefaultRouter

router = DefaultRouter()

from .views import HeaderTitleViewSet


router.register(r'header-title', HeaderTitleViewSet, basename="header-title")

urlpatterns = router.urls