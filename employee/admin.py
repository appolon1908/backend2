from django.contrib import admin

from .models import Employee, SocialMedia


class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'team', "employee_id", 'is_active', 'date_joined')
    search_fields = ('first_name', 'last_name', 'email', "employee_id", "team")
    list_filter = ('team',)



admin.site.register(Employee, EmployeeAdmin)
admin.site.register(SocialMedia)