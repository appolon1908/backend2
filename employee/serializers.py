from rest_framework import serializers
from rest_framework.fields import CharField
from rest_framework.pagination import LimitOffsetPagination

from django.conf import settings


from .models import Employee, SocialMedia





class SocialMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialMedia
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class CreateSocialMediaSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    link = serializers.URLField()
    
    
class EmployeeSerializer(serializers.ModelSerializer):
    socials = SocialMediaSerializer(many=True, read_only=True)
    
    def to_representation(self, instance):
        request = self.context.get('request')
        representation = super().to_representation(instance)
        # Add socials dynamically
        representation['socials'] = SocialMediaSerializer(
            instance.social_media_profiles.all(), many=True
        ).data
        
        profile_picture = (
            settings.BASE_URL+instance.profile_picture.url if instance.profile_picture else None)

        representation['profile_picture'] = profile_picture
        return representation
    
    class Meta:
        model = Employee
        fields = [
            'id', 'first_name', 
            'last_name', 'email', 
            'phone', 'team', 
            'employee_id', 'country', 
            'role', 'profile_picture', 
            'qr_code', 'extra_fields', 
            'date_of_birth', 'is_active', 
            'date_joined', 'updated_at', 'socials']
        read_only_fields = ['id', 'created_at', 'updated_at']



class CreateEmployeeSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    country = serializers.CharField(required=False)
    phone = serializers.CharField(max_length=15, required=False)
    team = serializers.CharField(required=False)
    date_of_birth = serializers.DateField(required=False)
    is_active = serializers.BooleanField(default=True)
    profile_picture = serializers.FileField(required=False)
    role= serializers.CharField(required=False)
    extra_fields = serializers.JSONField(required=False)
    social_media = serializers.ListField(child=CreateSocialMediaSerializer(), required=False)
    
    def validate_extra_fields(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Extra fields must be a dictionary.")
        
        for key, val in value.items():
            if not isinstance(key, str):
                raise serializers.ValidationError("Keys must be strings.")
            if not isinstance(val, str):  # Ensuring only string values (like CharField)
                raise serializers.ValidationError(f"Value for '{key}' must be a string.")
        
        return value
    
    
