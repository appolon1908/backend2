from django.contrib import admin


from .models import ElectronicBillingInterest, HeaderTitle, CaseStudy, FAQs, ContactUs, Logo, TaxPayer, Testimonial
from .odoo import sync_billing_interest, sync_contact, sync_taxpayer

admin.site.register(FAQs)
admin.site.register(Logo)
admin.site.register(Testimonial)
admin.site.register(CaseStudy)
admin.site.register(HeaderTitle)


@admin.register(ElectronicBillingInterest)
class ElectronicBillingInterestAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone", "uses_erp", "odoo_sync_status", "created_at")
    list_filter = ("uses_erp", "odoo_sync_status", "created_at")
    search_fields = ("full_name", "email", "phone")
    readonly_fields = ("odoo_sync_status", "odoo_record_id", "odoo_last_error", "odoo_synced_at", "created_at")
    actions = ("retry_odoo_delivery",)

    @admin.action(description="Retry delivery to Odoo")
    def retry_odoo_delivery(self, request, queryset):
        successful = sum(1 for item in queryset if sync_billing_interest(item))
        self.message_user(request, f"Delivered {successful} of {queryset.count()} selected submissions.")


@admin.register(ContactUs)
class ContactUsAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "company_size", "odoo_sync_status", "created_at")
    list_filter = ("odoo_sync_status", "created_at")
    search_fields = ("full_name", "email", "message")
    readonly_fields = ("odoo_sync_status", "odoo_record_id", "odoo_last_error", "odoo_synced_at", "created_at")
    actions = ("retry_odoo_delivery",)

    @admin.action(description="Retry delivery to Odoo")
    def retry_odoo_delivery(self, request, queryset):
        successful = sum(1 for item in queryset if sync_contact(item))
        self.message_user(request, f"Delivered {successful} of {queryset.count()} selected submissions.")


@admin.register(TaxPayer)
class TaxPayerAdmin(admin.ModelAdmin):
    list_display = ("name_of_tax_payer", "tax_payer_rnc", "tax_payer_email", "odoo_sync_status", "created_at")
    list_filter = ("odoo_sync_status", "created_at")
    search_fields = ("name_of_tax_payer", "trade_name", "tax_payer_rnc", "tax_payer_email")
    readonly_fields = ("odoo_sync_status", "odoo_record_id", "odoo_last_error", "odoo_synced_at", "created_at")
    actions = ("retry_odoo_delivery",)

    @admin.action(description="Retry delivery to Odoo")
    def retry_odoo_delivery(self, request, queryset):
        successful = sum(1 for item in queryset if sync_taxpayer(item))
        self.message_user(request, f"Delivered {successful} of {queryset.count()} selected registrations.")
