from django.conf import settings
from rest_framework import serializers
from .models import User, Visitor, BlacklistedIP



class UserSerializer(serializers.ModelSerializer):
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Invalid credentials, please try another value.')
        return value
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        profile_picture = instance.profile_picture.url if instance.profile_picture else None
        data['profile_picture'] = f"{settings.BASE_URL}{profile_picture}" if profile_picture else None
        return data
        
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone_number', 'client_id', 'created_at', 'updated_at', 'profile_picture', 'timezone', 'plan_type', 'trial_expiry_date', 'password']
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {'password': {'write_only': True}}
        
class GetUserSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        profile_picture = instance.profile_picture.url if instance.profile_picture else None
        data['profile_picture'] = f"{settings.BASE_URL}{profile_picture}" if profile_picture else None
        return data
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone_number', 'created_at', 'updated_at', 'profile_picture', 'timezone', 'plan_type', 'trial_expiry_date']
        read_only_fields = ['id', 'created_at', 'updated_at']
        

class GetShortUserDetailsSerializer(serializers.ModelSerializer):
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        profile_picture = instance.profile_picture.url if instance.profile_picture else None
        data['profile_picture'] = f"{settings.BASE_URL}{profile_picture}" if profile_picture else None
        return data
    
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'profile_picture']
        read_only_fields = ['id']
        
        
class VisitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visitor
        fields = "__all__"
        read_only_fields = ['id', 'created_at']
        
        
class BlacklistedIPSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlacklistedIP
        fields = "__all__"
        read_only_fields = ['id', 'created_at']
        
        
        
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()
    password = serializers.CharField()
    