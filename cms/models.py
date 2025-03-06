import uuid
from django.db import models


def generate_id():
    return uuid.uuid4().hex


class HeaderTitle(models.Model):
    title = models.CharField(max_length=256)
    description = models.TextField(blank=True)
    page = models.CharField(max_length=256, blank=True)
    image = models.ImageField(upload_to="cms/images", blank=True, null=True)
    video = models.FileField(upload_to="cms/videos", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    



class CaseStudy(models.Model):
    title = models.CharField(max_length=256)
    descriptiion = models.TextField()
    image = models.FileField(upload_to="cms/images")
    extra_fields = models.JSONField(verbose_name="extra-fields", default=dict, null=True, blank=True)
    
    def __str__(self):
        return self.title
    

class FAQs(models.Model):
    question = models.CharField(max_length=256)
    answer = models.TextField()
    
    class Meta:
        verbose_name = "Frequently Asked Question"
        verbose_name_plural = "Frequently Asked Questions"
    
    
class ContactUs(models.Model):
    full_name = models.CharField(max_length=256)
    email = models.EmailField(max_length=256)
    company_size = models.CharField(max_length=20, null=True, blank=True)
    message = models.TextField()
    
    def __str__(self):
        return self.full_name
    
    

class Logo(models.Model):
    logo = models.ImageField(upload_to="logo/")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    
class TaxPayer(models.Model):
    id = models.CharField(max_length=256, primary_key=True, default=generate_id, editable=False)
    address_reference = models.CharField(max_length=256, null=True, blank=True)
    visiting_hours = models.CharField(max_length=256, null=True, blank=True)
    
    # Legal representation
    representation_rnc = models.CharField(max_length=256, null=True, blank=True)
    name_of_representative = models.CharField(max_length=256, null=True, blank=True)
    representative_phone = models.CharField(max_length=256, null=True, blank=True)
    representative_cell_phone = models.CharField(max_length=256, null=True, blank=True)
    representative_email = models.CharField(max_length=256, null=True, blank=True)
    operation_carried_out_in_premise = models.CharField(max_length=256, null=True, blank=True)
    
    # store or warehouse data
    street_of_warehouse = models.CharField(max_length=256, null=True, blank=True) 
    store_or_warehouse_number = models.CharField(max_length=256, null=True, blank=True) 
    province_of_warehouse = models.CharField(max_length=256, null=True, blank=True) 
    warehouse_reference = models.CharField(max_length=256, null=True, blank=True) 
    local_administration = models.CharField(max_length=256, null=True, blank=True) 
    warehouse_sector = models.CharField(max_length=256, null=True, blank=True)
    
    tax_payer_rnc = models.CharField(max_length=256, null=True, blank=True)
    name_of_tax_payer = models.CharField(max_length=256, null=True, blank=True) 
    trade_name = models.CharField(max_length=256, null=True, blank=True)
    tax_payer_telephone = models.CharField(max_length=256, null=True, blank=True)
    tax_payer_cell_phone = models.CharField(max_length=256, null=True, blank=True)
    tax_payer_email = models.CharField(max_length=256, null=True, blank=True)
    tax_payer_number = models.CharField(max_length=256, null=True, blank=True)
    tax_payer_sector = models.CharField(max_length=256, null=True, blank=True)
    tax_payer_province = models.CharField(max_length=256, null=True, blank=True)
    
    

class TaxPayerMedia(models.Model):
    taxpayer = models.ForeignKey(TaxPayer, related_name="media_files", on_delete=models.CASCADE)
    media_file = models.FileField(upload_to="tax/images")
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Testimonial(models.Model):
    full_name = models.CharField(max_length=256)
    rating = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    message = models.TextField()
    role = models.CharField(max_length=256, null=True, blank=True)
    image = models.ImageField(upload_to="testimonials/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    meta_data = models.JSONField(null=True, blank=True)
    
    def __str__(self):
        return self.full_name