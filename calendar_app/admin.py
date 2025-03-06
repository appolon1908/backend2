from django.contrib import admin

from .models import Event


class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'start_time', 'end_time', 'event_type', 'created_by', 'employee', 'customer']
    list_filter = ['event_type', 'created_by', 'employee', 'customer']
    search_fields = ['title', 'description', 'created_by__email', 'employee__first_name', 'employee__last_name',
                     'customer__first_name', 'customer__last_name']
    
    
admin.site.register(Event, EventAdmin)