from django.urls import path
from rest_framework.routers import DefaultRouter

from blog_app.views import BlogViewSet
from blog_app.views import robots_txt

router = DefaultRouter()


router.register('', BlogViewSet, basename='blog')

urlpatterns = router.urls

urlpatterns += [path('robots.txt', robots_txt, name='robots_txt'),]