from .service import StripeService
from .serializers import PaymentSerializer

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .webhook import stripe_webhook
from django.conf import settings


from drf_yasg.utils import swagger_auto_schema




class PaymentViewSet(ViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Create a payment",
        operation_summary="Create a payment",
        tags=["Payment"],
        request_body=PaymentSerializer,
    )
    @action(methods=['POST'], detail=False, url_path='stripe-payment')
    def create_payment(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        name = serializer.data.get('name')
        email = serializer.data.get('email')
        amount = serializer.data.get('amount')

        stripe_service = StripeService()
        payment = stripe_service.create_payment_intent(
            amount=amount,
            email=email,
            name=name
        )
        
        return Response(
            {"client_secret": payment.get("client_secret")}, 
            status=status.HTTP_201_CREATED)

    @swagger_auto_schema(operation_description="Legacy compatibility alias for the payment endpoint")
    @action(methods=['POST'], detail=False, url_path='stipe-payment')
    def create_payment_legacy(self, request):
        return self.create_payment(request)
    
    
    @swagger_auto_schema(
        operation_description="Stripe webhook",
        operation_summary="Stripe webhook",
        tags=["Webhook"],
    )
    @action(methods=['POST'], detail=False, url_path="stripe-webhook", permission_classes=[AllowAny])
    def stripe_webhook(self, request):
        if len(request.body) > getattr(settings, "WEBHOOK_MAX_BODY_BYTES", 262144):
            return Response({"code": "payload_too_large"}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        return stripe_webhook(request)
