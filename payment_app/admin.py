from django.contrib import admin

from .models import Transaction



class TransactionAdmin(admin.ModelAdmin):
    list_display = ['amount', 'customer_email', 'status', 'payment_status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['amount', 'customer_email']
    
    

admin.site.register(Transaction, TransactionAdmin)