from django.contrib import admin
from .models import ChatLead, WebhookReceipt

class ReadOnlyIntakeAdmin(admin.ModelAdmin):
    def has_add_permission(self,request): return False
    def has_change_permission(self,request,obj=None): return False
    def has_delete_permission(self,request,obj=None): return False

@admin.register(ChatLead)
class ChatLeadAdmin(ReadOnlyIntakeAdmin):
    list_display=("id","location_id","contact_id","sms_consent","updated_at")
    list_filter=("location_id","sms_consent")
    search_fields=("contact_id","email","phone")

@admin.register(WebhookReceipt)
class WebhookReceiptAdmin(ReadOnlyIntakeAdmin):
    list_display=("id","event_type","status","received_at")
    list_filter=("status","event_type")
