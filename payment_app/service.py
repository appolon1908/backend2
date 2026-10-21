import logging
from decimal import Decimal, InvalidOperation

import stripe
from django.conf import settings

from .models import Transaction

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIP_SECRET_KEY


class PaymentConfigurationError(ValueError):
    pass


class StripeService:
    def __init__(self):
        self.stripe = stripe

    def create_customer(self, name, email):
        return self.stripe.Customer.create(name=name, email=email)

    def get_customer(self, email):
        return self.stripe.Customer.list(email=email)

    @staticmethod
    def resolve_authoritative_amount(product_code):
        catalog = getattr(settings, "PAYMENT_PRICE_CATALOG", {})
        if not isinstance(catalog, dict):
            raise PaymentConfigurationError("Payment price catalog is invalid")
        raw = catalog.get(product_code)
        if raw is None:
            raise PaymentConfigurationError("Unknown or unavailable product code")
        try:
            amount = Decimal(str(raw))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise PaymentConfigurationError("Configured product price is invalid") from exc
        quantized = amount.quantize(Decimal("0.01"))
        if amount != quantized or quantized <= 0:
            raise PaymentConfigurationError("Configured product price is invalid")
        return quantized

    def create_payment_intent(self, product_code, name, email, currency="usd"):
        amount = self.resolve_authoritative_amount(product_code)
        customer = self.create_customer(name=name, email=email)
        payment = self.stripe.PaymentIntent.create(
            amount=int(amount * 100),
            currency=currency,
            customer=customer.get("id"),
            metadata={"product_code": product_code},
        )
        Transaction.objects.create(
            amount=amount,
            transaction_id=payment.get("id"),
            customer_id=customer.get("id"),
            customer_email=email,
            client_secret=payment.get("client_secret"),
            payment_method=payment.get("payment_method"),
            status=payment.get("status"),
            currency=payment.get("currency"),
            meta_data={
                "product_code": product_code,
                "payment_method_configuration_details": payment.get(
                    "payment_method_configuration_details"
                ),
            },
        )
        return payment
