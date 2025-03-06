from django.conf import settings
from rest_framework import serializers
from .models import HeaderTitle, CaseStudy, FAQs, ContactUs, Logo, TaxPayer, Testimonial, TaxPayerMedia


class HeaderTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeaderTitle
        fields = "__all__"
        

class CaseStudySerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseStudy
        fields = "__all__"
        

class LogoSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        logo = instance.logo.url if instance.logo else None
        data['logo'] = f"{settings.BASE_URL}{logo}" if logo else None
        return data
    
    
    class Meta:
        model = Logo
        fields = "__all__"

class FaqSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQs
        fields = "__all__"
        

class ContactUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactUs
        fields = "__all__"



class TaxPayerMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxPayerMedia
        fields = ['id', 'media_file', 'uploaded_at']

class TaxPayerSerializer(serializers.ModelSerializer):
    media_files = TaxPayerMediaSerializer(many=True, read_only=True)
    class Meta:
        model = TaxPayer
        fields = [
            'media_files', 'id',
            'address_reference', 'visiting_hours', 'representation_rnc', 'name_of_representative',
            'name_of_representative', 'representative_phone', 'representative_cell_phone',
            'representative_email', 'operation_carried_out_in_premise', 'street_of_warehouse',
            'street_of_warehouse', 'store_or_warehouse_number', 'province_of_warehouse',
            'warehouse_reference', 'local_administration', 'warehouse_sector', 'tax_payer_rnc',
            'name_of_tax_payer', 'trade_name', 'tax_payer_telephone', 'tax_payer_cell_phone',
            'tax_payer_email', 'tax_payer_number', 'tax_payer_sector', 'tax_payer_province',
        ]
        
        
class TestimonialSerializer(serializers.ModelSerializer):
    
    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['image'] = f"{settings.BASE_URL}{instance.image.url}" if instance.image else None
        return response
    class Meta:
        model = Testimonial
        fields = "__all__"