"""
URL configuration for CORE project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.conf import settings
from django.conf.urls.static import static
from lead_capture.views import MetricsView, PrometheusMetricsView, ServiceManifestView, ServiceStatusView

from django.contrib.sitemaps.views import sitemap

from blog_app.sitemap import StaticSitemap, BlogSitemap


schema_view = get_schema_view(
   openapi.Info(
      title="Codstra API",
      default_version='v1',
      description="Codstra API",
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

sitemaps = {
    'tasks': BlogSitemap(),
    'static': StaticSitemap(),
}


urlpatterns = [
    path('healthz/', lambda request: JsonResponse({'status': 'ok'}), name='healthz'),
    path('health/live', ServiceStatusView.as_view(), {"check": "live"}, name='health-live'),
    path('health/ready', ServiceStatusView.as_view(), {"check": "ready"}, name='health-ready'),
    path('.well-known/codestra-service', ServiceManifestView.as_view(), name='service-manifest'),
    path('metrics', MetricsView.as_view(), name='metrics'),
    path('internal/metrics', PrometheusMetricsView.as_view(), name='prometheus-metrics'),
    path('admin/', admin.site.urls),
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='api-docs'),
    path('api/schema/', schema_view.without_ui(cache_timeout=0), name='api-schema'),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/blog/', include('blog_app.urls')),
    path('api/auth/', include('auth_app.urls')),
    path('api/employee/', include('employee.urls')),
    path('api/calendar/', include('calendar_app.urls')),
    path('api/cms/', include('cms.urls')),
    path('api/hero/', include('hero.urls')),
    path('api/customers/', include('customers.urls')),
    path('api/career/', include('career_app.urls')),
    path('api/payment/', include('payment_app.urls')),
    path('api/v1/', include('lead_capture.urls')),
    path('internal/v1/', include('lead_capture.internal_urls')),
    path('api/career/', include('career_app.urls')),
    path(
    "sitemap.xml",
    sitemap,
    {"sitemaps": sitemaps},
    name="django.contrib.sitemaps.views.sitemap",
)
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
