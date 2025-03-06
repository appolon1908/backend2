from django.contrib import admin

from .models import User, Visitor


class UserAdmin(admin.ModelAdmin):
    list_display = ["first_name", "last_name", "email", "client_id", "is_active", "is_superuser"]
    



admin.site.register(User, UserAdmin)
admin.site.register(Visitor)
