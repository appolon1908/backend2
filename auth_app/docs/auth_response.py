from rest_framework import serializers

from drf_yasg import openapi


login_success_response = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'user': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'profile_picture': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                'timezone': openapi.Schema(type=openapi.TYPE_STRING),
                'plan_type': openapi.Schema(type=openapi.TYPE_STRING),
                'trial_expiry_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
            }
        ),
        'token': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                'access': openapi.Schema(type=openapi.TYPE_STRING),
            }
        )
    }
)

login_error_response = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'error': openapi.Schema(type=openapi.TYPE_STRING)
    }
)


LOGIN_RESPONSE = {
    201 : openapi.Response(
        description="User logged in successfully",
        schema=login_success_response
    ),
    400 : openapi.Response(
        description="Invalid credentials",
        schema=login_error_response
    )
}
