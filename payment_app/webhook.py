import stripe
import logging
from django.conf import settings
from django.http import JsonResponse, HttpResponse

from .models import Transaction


logger = logging.getLogger(__name__)

def stripe_webhook(request):
    payload = request.body
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
            
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        
        # get Transaction instance
        transaction = Transaction.objects.filter(
            customer_id=payment_intent.get('customer'),
            transaction_id=payment_intent.get('id'),
            client_secret=payment_intent.get('client_secret')).first()
        
        if not transaction:
            return HttpResponse(status=400)
        
        transaction.status = payment_intent.get('status')
        transaction.payment_status = 'succeeded'
        transaction.save()
        logger.info(f"PaymentIntent was successful: {payment_intent}")
        print('PaymentIntent was successful:', payment_intent)
        # Update order status or perform other logic here

    elif event['type'] == 'payment_intent.payment_failed':
        print('Payment failed.')
        # Handle failed payment case

    return HttpResponse(status=200)