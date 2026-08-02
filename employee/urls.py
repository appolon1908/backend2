from rest_framework.routers import DefaultRouter
from .views import EmployeeViewset

router = DefaultRouter()
router.register(r'', EmployeeViewset, basename='employee')

urlpatterns = router.urls
