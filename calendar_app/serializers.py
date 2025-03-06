from rest_framework import serializers
from .models import Event

from employee.serializers import EmployeeSerializer



class EventSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer(read_only=True)
    class Meta:
        model = Event
        fields = "__all__"
        
        
class CreateEventSerializer(serializers.Serializer):
    employee_id = serializers.CharField()
    title = serializers.CharField()
    event_type = serializers.ChoiceField(choices=Event.EVENT_TYPE, default="meeting")
    description = serializers.CharField()
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    
        

