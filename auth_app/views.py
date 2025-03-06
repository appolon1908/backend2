import uuid
from rest_framework import status
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.pagination import LimitOffsetPagination
import requests
from django.db import models
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password

from .models import User, Visitor, BlacklistedIP
from .serializers import (
                UserSerializer, VisitorSerializer, 
                ResetPasswordSerializer,
                GetUserSerializer, BlacklistedIPSerializer, 
                ForgotPasswordSerializer)

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from auth_app.docs.auth_response import LOGIN_RESPONSE

from helpers.cache_manager import CacheManager
from notification.service import EmailService


class AuthViewSet(ViewSet):
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Sign up user",
        operation_summary="Sign up user",
        tags=["Auth"],
        request_body=UserSerializer,
    )
    @action(detail=False, methods=['POST'])
    def signup(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # check user does not exist
        if User.objects.filter(email=serializer.validated_data['email']).exists():
            return Response({'message': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        
        # user = User.objects.create_user(
        #     email=serializer.validated_data['email'],
        #     first_name=serializer.validated_data['first_name'],
        #     last_name=serializer.validated_data['last_name'],
        #     phone_number=serializer.validated_data.get('phone_number'),
        #     password=serializer.validated_data['password'],
        #     timezone=serializer.validated_data.get('timezone'),
        # )
        
    
        #Sent to odoo>

        odoo_data = {
            'first_name': f"{request.data['first_name']}", 
            'last_name': f"{request.data['last_name']}",
            'email': request.data['email'],
            'phone': request.data.get('phone_number'),
            'plan_type': request.data.get('plan_type', 'FREE'), 
            #'profile_picture': profile_picture 
    }

        odoo_api_url = "https://crm.codestra.co/api/website/register"  
        odoo_response = requests.post(odoo_api_url, json=odoo_data)

        if odoo_response.status_code == 200:
            try:
                odoo_response_data = odoo_response.json()
                odoo_client_id = odoo_response_data.get("result", {}).get('id')

                if odoo_client_id:
                    
                    user = User.objects.create_user(
                    email=serializer.validated_data['email'],
                    first_name=serializer.validated_data['first_name'],
                    last_name=serializer.validated_data['last_name'],
                    phone_number=serializer.validated_data.get('phone_number'),
                    password=serializer.validated_data['password'],
                    timezone=serializer.validated_data.get('timezone'),
                    odoo_id=odoo_client_id,  
                )
                   
                    profile_picture = request.FILES.get('profile_picture')
                   
                    if profile_picture:
                        user.profile_picture.save(profile_picture.name, profile_picture)

                    return Response({
                        "message": "Sign up successful",
                        "odoo_client_id": odoo_client_id
                },      status=status.HTTP_201_CREATED)

                else:
                    return Response({
                    "message": "Error: No Odoo ID returned",
                    "error": "Odoo API did not return a valid client ID"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            except ValueError as e:
                return Response({
                    "message": "Error processing Odoo response",
                    "error": str(e)
            },      status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
        else:
            return Response({
                "message": "Error communicating with Odoo",
                "error": f"Odoo API returned status code {odoo_response.status_code}"
        },      status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

    @swagger_auto_schema(
        operation_description="log in user",
        operation_summary="log in user",
        tags=["Auth"],
        request_body=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address'),
                    'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
                },
                required=['email', 'password']
            ),
        responses=LOGIN_RESPONSE
    )
    @action(detail=False, methods=['POST'])
    def login(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'message': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        
        user_password = check_password(password, user.password)
        if not user_password:
            return Response(errors={"error": "incorrect email/password"}, status=status.HTTP_400_BAD_REQUEST)
        
        token = RefreshToken.for_user(user)
        data = {
            "user": GetUserSerializer(instance=user).data,
            "token": {"refresh": str(token), "access": str(token.access_token)},
        }

        return Response(data, status=status.HTTP_200_OK)
    
    
    @swagger_auto_schema(
        operation_description="Log Out user",
        operation_summary="Log Out user",
        tags=["Auth"],
        request_body=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='refresh_token'),
                },
                required=['refresh']
            )
    )
    @action(detail=False, methods=['POST'])
    def logout(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Endpoint for users who forgot their password",
        operation_summary="Endpoint for users who forgot their password",
        tags=["Auth"],
        request_body=ForgotPasswordSerializer,
    )
    @action(detail=False, methods=['POST'], url_path='forgot-password')
    def forgot_password(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        users = User.objects.filter(email=serializer.validated_data['email'])
        if not users.exists():
            return Response({"error": "invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        
        
        user = users.first()
        code = uuid.uuid4().hex[:6].upper()
        CacheManager.set_key(
            f"user:reset_password:{code}",
            {"email": user.email},
            86400,
        )
        EmailService.send_async(
            "forgot_password.html",
            "Forgot Password",
            [user.email],
            {
                "first_name": user.first_name.capitalize(),
                "code": code,
            },
        )
        return Response({"message": "Reset password token sent to email"}, status=status.HTTP_200_OK)


    @swagger_auto_schema(
        operation_description="Reset password endpoint",
        operation_summary="Reset password endpoint",
        tags=["Auth"],
        request_body=ResetPasswordSerializer,
    )
    @action(detail=False, methods=['POST'], url_path='reset-password')
    def reset_password(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        
        cached_code = CacheManager.retrieve_key(f"user:reset_password:{code}")
        
        if cached_code:
            if email == cached_code.get('email'):
                user = User.objects.filter(email=email).first()
                
                user.set_password(password)
                user.save()
                
                CacheManager.delete_key(f"user:reset_password:{code}")
                return Response({"message": "Password reset successful"})
            else:
                return Response({"error": "Invalid email or code"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Invalid email or code"}, status=status.HTTP_400_BAD_REQUEST)        

class UserViewSet(ViewSet):
    permission_classes = [IsAuthenticated]
    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        operation_description="List Users",
        operation_summary="List Users",
        tags=["Auth"],
    )
    def list(self, request):
        users = User.objects.all()
        return Response(UserSerializer(users, many=True).data)
    
    @swagger_auto_schema(
        operation_description="Retrieve User",
        operation_summary="Retrieve User",
        tags=["Auth"],
    )
    def retrieve(self, request, pk=None):
        user = User.objects.filter(id=pk).first()
        serializer = UserSerializer(user)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="User details",
        operation_summary="User details",
        tags=["Auth"],
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)
    

    @swagger_auto_schema(
        operation_description="Update user",
        operation_summary="Update user",
        tags=["Auth"],
        request_body=UserSerializer
    )
    def update(self, request, pk=None):
        user = User.objects.filter(id=pk).first()
        serializer = UserSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        user.email = serializer.validated_data.get('email', user.email)
        user.first_name = serializer.validated_data.get('first_name', user.first_name)
        user.last_name = serializer.validated_data.get('last_name', user.last_name)
        user.phone_number = serializer.validated_data.get('phone_number', user.phone_number)

        user.is_active = serializer.validated_data.get('is_active', user.is_active)
        user.is_staff = serializer.validated_data.get('is_staff', user.is_staff)
        user.is_superuser = serializer.validated_data.get('is_superuser', user.is_superuser)
        user.save()
        return Response(UserSerializer(user).data)
    
    @swagger_auto_schema(
        operation_description="Delete User",
        operation_summary="Delete User",
        tags=["Auth"],
    )
    def destroy(self, request, pk=None):
        user = User.objects.filter(id=pk).first()
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class VisitorViewSet(ViewSet):
    pagination_class = LimitOffsetPagination
    
    @swagger_auto_schema(
        operation_description="List all visitors",
        operation_summary="List all visitors",
        tags=["Visitors"],
    )
    def list(self, request):
        paginator = self.pagination_class()
        visitors = Visitor.objects.all().order_by('-visited_at')
        
        result_page = paginator.paginate_queryset(visitors, request)
        
        if result_page is not None:
            serializer = VisitorSerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        return Response(VisitorSerializer(visitors, many=True).data)
    
    
    @swagger_auto_schema(
        operation_description="List all visitors by their IP addresses",
        operation_summary="List all visitors by their IP addresses",
        tags=["Visitors"],
    )
    @action(detail=False, methods=['get'], url_path="visitors-ips")
    def list_ip(self, request):
        # Retrieve distinct IP addresses
        visitors = (
            Visitor.objects.values("ip_address")
            .annotate(
                visit_count=models.Count("ip_address"),
                latest_id=models.Max("id"),  # Get the latest visit ID for each IP
            )
            .order_by("-latest_id")  # Sort by latest visit for consistent results
        )

        # Retrieve the full details of the latest visit for each IP
        latest_visit_ids = [v["latest_id"] for v in visitors]
        visitor_details = Visitor.objects.filter(id__in=latest_visit_ids)

        # Apply pagination to the queryset
        paginator = self.pagination_class()
        paginated_visitor_details = paginator.paginate_queryset(visitor_details, request)

        # Serialize the paginated data
        serializer = VisitorSerializer(paginated_visitor_details, many=True)
        serialized_data = serializer.data

        # Add the visit_count to each visitor record
        for visitor in serialized_data:
            visitor["visit_count"] = next(
                v["visit_count"] for v in visitors if v["ip_address"] == visitor["ip_address"]
            )

        # Return the paginated response
        return paginator.get_paginated_response(serialized_data)

    @swagger_auto_schema(
        operation_description="Block an IP address from visiting",
        operation_summary="Block an IP address from visiting",
        tags=["Visitors"],
        request_body=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'ip_address': openapi.Schema(type=openapi.TYPE_STRING, description='IP address'),
                },
                required=['ip_address']
            ),
    )
    @action(detail=False, methods=['post'], url_path="blacklist-ip")
    def blacklist(self, request):
        ip_address = request.data.get("ip_address")
        if not ip_address:
            return Response({"error": "IP address is required"}, status=status.HTTP_400_BAD_REQUEST)

        if BlacklistedIP.objects.filter(ip_address=ip_address).exists():
            return Response({"message": "IP address is already blacklisted."})

        BlacklistedIP.objects.create(ip_address=ip_address)
        return Response({"message": f"IP address {ip_address} has been blacklisted."}, status=status.HTTP_201_CREATED)
    
    @swagger_auto_schema(
        operation_description="List all blacklisted IP addresses",
        operation_summary="List all blacklisted IP addresses",
        tags=["Visitors"],
    )
    @action(detail=False, methods=['get'], url_path="blacklisted-ips")
    def blacklisted(self, request):
        blacklisted_ips = BlacklistedIP.objects.all()
        return Response(BlacklistedIPSerializer(blacklisted_ips, many=True).data)
    
    
    @swagger_auto_schema(
        operation_description="Whitelist a blacklisted IP address",
        operation_summary="Whitelist a blacklisted IP address",
        tags=["Visitors"],
        request_body=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'ip_address': openapi.Schema(type=openapi.TYPE_STRING, description='IP address'),
                },
                required=['ip_address']
            ),
    )
    @action(detail=False, methods=['POST'], url_path="whitelist-ips")
    def whitelist_ip(self, request):
        ip_address = request.data.get("ip_address")
        if not ip_address:
            return Response({"error": "IP address is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not BlacklistedIP.objects.filter(ip_address=ip_address).exists():
            return Response({"message": "IP address is not blacklisted."})

        BlacklistedIP.objects.filter(ip_address=ip_address).delete()
        return Response({"message": f"IP address {ip_address} has been whitelisted."}, status=status.HTTP_200_OK)