from rest_framework import serializers

from .models import Customer
from calendar_app.models import Event
from calendar_app.serializers import EventSerializer



class CustomerSerializer(serializers.ModelSerializer):
    events = serializers.SerializerMethodField(read_only=True)
    
    def get_events(self, obj):
        events = Event.objects.filter(customer=obj)
        return EventSerializer(events, many=True).data
    
    class Meta:
        model = Customer
        fields = "__all__"