import qrcode
from io import BytesIO

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.pagination import LimitOffsetPagination

from django.core.files import File
from django.conf import settings

from drf_yasg.utils import swagger_auto_schema


from .models import Employee, SocialMedia
import requests

from calendar_app.models import Event
from calendar_app.serializers import EventSerializer
from .serializers import (
            EmployeeSerializer, 
            SocialMediaSerializer, 
            CreateEmployeeSerializer, 
            CreateSocialMediaSerializer,
            )

from cms.models import HeaderTitle
from cms.serializers import HeaderTitleSerializer





class EmployeeViewset(viewsets.ViewSet):
    serializer_class = EmployeeSerializer
    pagination_class = LimitOffsetPagination

    def get_permissions(self):
        return [AllowAny()] if self.action in {'list', 'retrieve'} else [IsAdminUser()]
    
    def get_queryset(self):
        return Employee.objects.filter(is_active=True).order_by('-date_joined')
    
    #Sent to odoo funtions:
    def send_get_all_employees_to_odoo(self):
        odoo_url = f"{settings.ODOO_BASE_URL}/api/employees"
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.ODOO_API_TOKEN}'
        }

        try:
            response = requests.get(odoo_url, headers=headers, timeout=10)
            if response.status_code == 200:
                response_data = response.json()

                if response_data == []:
                    print("Error getting data from Odoo: No employees available")
                    return {"error": "No employees available"}
                elif response_data == {}:
                    print("Error getting data from Odoo: Empty response")
                    return {"error": "Empty response from Odoo"}
                
                return response_data

            else:
                print(f"Error getting data from Odoo: {response.status_code} - {response.text}")
                return {"error": f"Error from Odoo: {response.status_code} - {response.text}"}

        except requests.exceptions.RequestException as e:
            print(f"Error connecting to Odoo: {e}")
            return {"error": f"Error connecting to Odoo: {e}"}

    
    def send_get_employee_by_id_to_odoo(self, employee_id):
        odoo_url = f"{settings.ODOO_BASE_URL}/api/employees?id={employee_id}"
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.ODOO_API_TOKEN}'
        }

        try:
            response = requests.get(odoo_url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting data from Odoo: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to Odoo: {e}")
            return None

    
    def send_calendar_event_to_odoo(self, employee_id):
        odoo_url = f"{settings.ODOO_BASE_URL}/api/calendar_events?employee_id={employee_id}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.ODOO_API_TOKEN}'
        }

        try:
            response = requests.get(odoo_url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting events from Odoo: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to Odoo: {e}")
            return None

   
    def send_add_calendar_event_to_odoo(self, event_data):
        odoo_url = f"{settings.ODOO_BASE_URL}/api/website/add-activity"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.ODOO_API_TOKEN}'
        }

        try:
           
            response = requests.post(odoo_url, headers=headers, json=event_data, timeout=10)

          
            if response.status_code == 200:
                return response.json()
            else:
               
                print(f"Error adding event to Odoo: {response.status_code} - {response.text}")
                return response.json()  
        except requests.exceptions.RequestException as e:
          
            print(f"Error connecting to Odoo: {e}")
            return None
        
    
    @swagger_auto_schema(
        operation_description="List all employees",
        operation_summary="List all employees",
        tags=["Employee"],
    )
    # @action(methods=['GET'], detail=False, url_path='employees')
    def list(self, request):
        # paginator = self.pagination_class()
        # employees = self.get_queryset()
        
        # result_page = paginator.paginate_queryset(employees, request)

        # if result_page is not None:
        #     serializer = EmployeeSerializer(result_page, many=True)
        #     return paginator.get_paginated_response(serializer.data)
        
        # return Response(EmployeeSerializer(blogs, many=True).data)
        odoo_response = self.send_get_all_employees_to_odoo()

        if not odoo_response or (isinstance(odoo_response, dict) and "error" in odoo_response):
            employees = self.get_queryset()
            return Response(EmployeeSerializer(employees, many=True).data, status=status.HTTP_200_OK)
    
    # If everything is fine, return the data obtained
        return Response(odoo_response, status=status.HTTP_200_OK)
    
    
    @swagger_auto_schema(
        operation_description="Retrieve an employee by id",
        operation_summary="Retrieve an employee by id",
        tags=["Employee"],
    )
    # @action(methods=['GET'], detail=False, url_path='employees/(?P<pk>[a-z,A-Z,0-9]+)')
    def retrieve(self, request, pk=None):
        # employee = Employee.objects.prefetch_related('social_media_profiles').filter(id=pk).first()
        # serializer = EmployeeSerializer(employee)
        # return Response(serializer.data)
        
        #Adaptation to odoo:

        odoo_response = self.send_get_employee_by_id_to_odoo(pk)

        if odoo_response:
            return Response(odoo_response, status=status.HTTP_200_OK)
        employee = Employee.objects.prefetch_related('social_media_profiles').filter(id=pk).first()
        if not employee:
            return Response({"error": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(EmployeeSerializer(employee).data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Create an employee record form",
        operation_summary="Create an employee record form",
        tags=["Employee"],
        request_body=CreateEmployeeSerializer
    )
    # @action(methods=['POST'], detail=False, url_path='employees/')
    def create(self, request):
        serializer = CreateEmployeeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        socials = []
        if serializer.validated_data.get('social_media'):
            socials = serializer.validated_data.pop('social_media')
            
        if Employee.objects.filter(email=serializer.validated_data.get("email")).exists():
            return Response({'message': 'Employee email already exists'}, status=status.HTTP_400_BAD_REQUEST)
        
        employee = Employee.objects.create(**serializer.validated_data)
        
        # Generate QR code
        qr_data = f"{request.build_absolute_uri(f'/employee/{employee.id}/')}"
        
        qr = qrcode.make(qr_data)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        buffer.seek(0)

        # Save QR code to employee
        employee.qr_code.save(f"employee_{employee.id}_qrcode.png", File(buffer), save=True)
        
        if socials:
            social_media_objects = [SocialMedia(employee=employee, **social) for social in socials]
            SocialMedia.objects.bulk_create(social_media_objects)
        
        return Response({'message': 'Employee created successfully'}, status=status.HTTP_201_CREATED)
    
    
    
    @swagger_auto_schema(
        operation_description="Add social media link to employee",
        operation_summary="Add social media link to employee",
        tags=["Employee"],
        request_body=CreateSocialMediaSerializer
    )
    @action(methods=['POST'], detail=True, url_path="add-social-media")
    def add_social_media(self, request, pk=None):
        employee = Employee.objects.filter(id=pk).first()
        if not employee:
            return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = CreateSocialMediaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        SocialMedia.objects.create(employee=employee, **serializer.validated_data)
        
        return Response({'message': 'Social media link added successfully'}, status=status.HTTP_201_CREATED)
    
    
    @swagger_auto_schema(
        operation_description="Remove social media link from employee",
        operation_summary="Remove social media link from employee",
        tags=["Employee"],
    )
    @action(methods=['DELETE'], detail=True, url_path='remove-social-media/(?P<social_media_id>[^/.]+)')
    def remove_social_media(self, request, pk=None, social_media_id=None):
        employee = Employee.objects.filter(id=pk).first()
        if not employee:
            return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)
        
        social_media = SocialMedia.objects.filter(id=social_media_id, employee=employee).first()
        if not social_media:
            return Response({'error': 'Social media link not found'}, status=status.HTTP_404_NOT_FOUND)
        
        social_media.delete()
        
        return Response({'message': 'Social media link removed successfully'}, status=status.HTTP_204_NO_CONTENT)
    
    
    @swagger_auto_schema(
        operation_description="Get calendar event for an employee",
        operation_summary="Get calendar event for an employee",
        tags=["Employee"],
    )
    @action(methods=['GET'], detail=True)
    def calendar(self, request, pk=None):
        # employee = Employee.objects.filter(id=pk).first()
        
        # if not employee:
        #     return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # calendar = Event.objects.filter(employee=employee)
        
        # result_page = paginator.paginate_queryset(calendar, request)
        # if result_page is not None:
        #     serializer = EventSerializer(result_page, many=True)
        #     return paginator.get_paginated_response(serializer.data)
        
        # return Response(EventSerializer(calendar, many=True).data)

        #Odo part.

        odoo_response = self.send_calendar_event_to_odoo(pk)

        if odoo_response:
            return Response(odoo_response, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Error getting events Odoo."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
        
    @swagger_auto_schema(
        operation_description="Add calendar event for an employee",
        operation_summary="Add calendar event for an employee",
        tags=["Employee"],
        request_body=EventSerializer
    )
    @action(methods=['POST'], detail=True, url_path="add-calendar")
    def add_calendar(self, request, pk):
        # #paginator = self.pagination_class()
        # employee = Employee.objects.filter(id=pk).first()
        
        # if not employee:
        #     return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # serializer = EventSerializer(data=request.data)
        # serializer.is_valid(raise_exception=True)
        
        # event = Event.objects.create(employee=employee, **serializer.validated_data)
        # return Response(EventSerializer(event).data, status=status.HTTP_201_CREATED)


        #Adaptacion para odoo:

        try:
            
            serializer = EventSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
    
            event_data = serializer.validated_data
            
            event_data["start_date"] = event_data["start_date"].replace(tzinfo=None).isoformat()
            event_data["end_date"] = event_data["end_date"].replace(tzinfo=None).isoformat()
            
            event_data["customer_id"] = request.user.odoo_id
    
            try:
               
                odoo_response = self.send_add_calendar_event_to_odoo(event_data)
        
                
                if odoo_response:
                    return Response(odoo_response, status=status.HTTP_201_CREATED)
                else:
                    return Response({"error": "Error adding event to Odoo."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
            except Exception as odoo_error:
                return Response({"error": f"Error contacting Odoo: {str(odoo_error)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"error": f"Error processing request: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        
    
    @swagger_auto_schema(
        operation_description="Get Hero header title for employee page",
        operation_summary="Get Hero header title for employee page",
        tags=["Employee"],
    )
    @action(detail=False, methods=['get'], url_path="hero/header-title/get")
    def get_blog_header_title(self, request):
        header_title = HeaderTitle.objects.filter(page='blog').order_by('-created_at').first()
        
        if not header_title:
            return Response({'message': 'No header title found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(HeaderTitleSerializer(header_title).data, status=status.HTTP_200_OK)
    
    
    @swagger_auto_schema(
        operation_description="Create Hero Header Title for employee page",
        operation_summary="Create Hero Header Title for employee page",
        tags=["Employee"],
        request_body=HeaderTitleSerializer
    )
    @action(detail=False, methods=['post'], url_path="hero/header-title")
    def create_blog_header_title(self, request):
        serializer = HeaderTitleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(page='employee')
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
