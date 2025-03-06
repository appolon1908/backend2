from django.contrib import admin

from .models import Blog, Tag, Category

class BlogAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'status', 'published_at', 'scheduled_date']
    list_filter = ['status', 'published_at', 'scheduled_date']
    search_fields = ['title', 'author__email', 'author__first_name', 'author__last_name']



admin.site.register(Blog, BlogAdmin)
admin.site.register(Tag)
admin.site.register(Category)