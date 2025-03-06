from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Blog

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
        return ['api-root', 'blog-list', 'blog-list'] 

    def location(self, item):
        return reverse(item)