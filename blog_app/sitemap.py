from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Blog
from lead_capture.routing import INDUSTRIES

class BlogSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Blog.objects.all()

    def lastmod(self, obj):
        return obj.updated_at 

class StaticSitemap(Sitemap):
    priority = 0.5
    changefreq = 'monthly'

    def items(self):
        base = ['api-root', 'blog-list', '/ai-receptionist', '/pricing', '/book-demo', '/request-pricing', '/contact', '/thank-you', '/security', '/privacy', '/terms', '/industries']
        return [*base, *(f'/industries/{item["slug"]}' for item in INDUSTRIES.values())]

    def location(self, item):
        return item if item.startswith('/') else reverse(item)
