import stripe
import logging
from decimal import Decimal
from django.conf import settings
from .models import Transaction

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIP_SECRET_KEY


class StripeService:
    def __init__(self):
        self.stripe = stripe
        
    
    def create_customer(self, name, email):
        return self.stripe.Customer.create(name=name, email=email)
    
    def get_customer(self, email):
        return self.stripe.Customer.list(email=email)
    

    def create_payment_intent(self, amount, name, email, currency='usd'):
        
        try:
            # create customer first
            customer = self.create_customer(name=name, email=email)
            
            
            payment = self.stripe.PaymentIntent.create(
                amount=int(float(amount)) * 100,
                currency=currency,
                customer=customer.get("id"),
            )
            # create transaction instance
            transaction = Transaction.objects.create(
                amount=Decimal(amount),
                transaction_id=payment.get("id"),
                customer_id=customer.get("id"),
                customer_email=email,
                payment_method=payment.get("payment_method"),
                status=payment.get("status"),
                currency=payment.get("currency"),
                client_secret=payment.get("client_secret"), #TODO: encrypt this
                meta_data=payment.get("payment_method_configuration_details")
            )
            return payment
        except Exception as e:
            logger.error(e)
            return {"error": str(e)}
