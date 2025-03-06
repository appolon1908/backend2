from .service import StripeService
from .serializers import PaymentSerializer

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from .webhook import stripe_webhook


from drf_yasg.utils import swagger_auto_schema




class PaymentViewSet(ViewSet):
    serializer_class = PaymentSerializer

    @swagger_auto_schema(
        operation_description="Create a payment",
        operation_summary="Create a payment",
        tags=["Payment"],
        request_body=PaymentSerializer,
    )
    @action(methods=['POST'], detail=False, url_path='stipe-payment')
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
    
    
    @swagger_auto_schema(
        operation_description="Stripe webhook",
        operation_summary="Stripe webhook",
        tags=["Webhook"],
    )
    @action(methods=['POST'], detail=False, url_path="stripe-webhook")
    def stripe_webhook(self, request):
        stripe_webhook(request)
        return Response(status=status.HTTP_200_OK)
