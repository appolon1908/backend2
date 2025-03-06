from rest_framework.routers import DefaultRouter
from .views import EmployeeViewset

router = DefaultRouter(trailing_slash=False)
router.register(r'', EmployeeViewset, basename='employee')

urlpatterns = router.urls