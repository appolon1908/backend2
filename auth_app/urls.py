from rest_framework.routers import DefaultRouter

from .views import UserViewSet, AuthViewSet, VisitorViewSet

router = DefaultRouter()

router.register('users', UserViewSet, basename='users')
router.register('visitors', VisitorViewSet, basename='visitors')
router.register('', AuthViewSet, basename='auth')


urlpatterns = router.urls
