from .models import Customer
from .serializer import CustomerSerializer

from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action



from calendar_app.models import Event
from calendar_app.serializers import EventSerializer

from drf_yasg.utils import swagger_auto_schema

from notification.service import EmailService
from rest_framework.permissions import IsAuthenticated




class CustomerViewSet(ViewSet):
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="List all customers",
        operation_summary="List all customers",
        tags=["Customer"],
        )
    def list(self, request):
        customers = Customer.objects.all()
        serializer = self.serializer_class(customers, many=True)
        return Response(serializer.data)


    @swagger_auto_schema(
        operation_description="Retrieve a customer",
        operation_summary="Retrieve a customer",
        tags=["Customer"],
        )
    def retrieve(self, request, pk=None):
        customer = Customer.objects.filter(id=pk).first()
        if customer is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(customer)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Create a customer",
        operation_summary="Create a customer",
        tags=["Customer"],
        )
    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    @swagger_auto_schema(
        operation_description="Update a customer",
        operation_summary="Update a customer",
        tags=["Customer"],
        )
    def update(self, request, pk=None):
        customer = Customer.objects.filter(id=pk).first()
        if customer is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(customer, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
    @swagger_auto_schema(
        operation_description="List all the events of a customer",
        operation_summary="List all the events of a customer",
        tags=["Customer"],
        )
    @action(detail=True, methods=['get'])
    def events(self, request, pk=None):
        customer = Customer.objects.filter(id=pk).first()
        if customer is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        events = Event.objects.filter(customer=customer)
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Create an event for a customer",
        operation_summary="Create an event for a customer",
        tags=["Customer"],
        )
    @action(detail=True, methods=['post'], url_path="create-event")
    def create_event(self, request, pk=None):
        customer = Customer.objects.filter(id=pk).first()
        if customer is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = EventSerializer(data=request.data)
        if serializer.is_valid():
            
            if Event.objects.filter(
                title=serializer.validated_data.get('title'),
                customer=customer,
                start_time=serializer.validated_data.get('start_time'),
                ).exists():
                return Response({'error': 'Event already exists'}, status=status.HTTP_400_BAD_REQUEST)
            
            event = Event.objects.create(customer=customer, **serializer.validated_data)
            
            EmailService.send_async(
                subject=f"Event created for {customer.first_name} {customer.last_name}",
                template="event_notification.html",
                recipients=[customer.email, request.user.email],
                context={
                    "username": customer.first_name,
                    "event_name": event.title,
                    "event_date": event.start_time,
                }
            )
            return Response(EventSerializer(event).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)