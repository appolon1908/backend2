from .service import PaymentConfigurationError, StripeService
from .serializers import PaymentSerializer

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from .webhook import stripe_webhook

from drf_yasg.utils import swagger_auto_schema


class PaymentViewSet(ViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Create a payment from a server-authoritative product price",
        operation_summary="Create a payment",
        tags=["Payment"],
        request_body=PaymentSerializer,
    )
    @action(methods=["POST"], detail=False, url_path="stipe-payment")
    def create_payment(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        stripe_service = StripeService()
        try:
            payment = stripe_service.create_payment_intent(
                product_code=serializer.validated_data["product_code"],
                email=serializer.validated_data["email"],
                name=serializer.validated_data["name"],
            )
        except PaymentConfigurationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response(
                {"error": "Payment provider is temporarily unavailable"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {"client_secret": payment.get("client_secret")},
            status=status.HTTP_201_CREATED,
        )

    @swagger_auto_schema(
        operation_description="Stripe webhook",
        operation_summary="Stripe webhook",
        tags=["Webhook"],
    )
    @action(methods=["POST"], detail=False, url_path="stripe-webhook", permission_classes=[AllowAny])
    def stripe_webhook(self, request):
        return stripe_webhook(request)
