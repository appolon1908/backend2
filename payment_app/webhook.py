import stripe
import logging
import hashlib
from django.db import transaction as db_transaction
from django.utils import timezone
from django.conf import settings
from django.http import HttpResponse

from .models import StripeWebhookEvent, Transaction


logger = logging.getLogger(__name__)

def stripe_webhook(request):
    if request.method != "POST":
        return HttpResponse(status=405)
    payload = request.body
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    if not endpoint_secret or not sig_header:
        return HttpResponse(status=400)

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
            
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    event_id = event.get("id")
    if not event_id:
        return HttpResponse(status=400)
    event_type = event.get("type", "")
    payload_hash = hashlib.sha256(payload).hexdigest()

    # Stripe retries delivery. Claim each event exactly once, while allowing
    # a failed processing attempt to be retried by returning 5xx below.
    with db_transaction.atomic():
        receipt, created = StripeWebhookEvent.objects.select_for_update().get_or_create(
            event_id=event_id,
            defaults={"event_type": event_type, "payload_sha256": payload_hash},
        )
        if not created and receipt.payload_sha256 != payload_hash:
            logger.error("Stripe event payload changed for %s", event_id)
            return HttpResponse(status=400)
        if not created and receipt.status == "processed":
            return HttpResponse(status=200)
        receipt.attempts += 1
        receipt.status = "processing"
        receipt.last_error = ""
        receipt.save(update_fields=["attempts", "status", "last_error"])

    try:
      # Handle the event
      if event_type == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        
        # get Transaction instance
        transaction = Transaction.objects.filter(
            customer_id=payment_intent.get('customer'),
            transaction_id=payment_intent.get('id'),
        ).first()
        
        if not transaction:
            logger.warning("Stripe event %s has no local transaction", event_id)
        else:
            transaction.status = payment_intent.get('status')
            transaction.payment_status = 'success'
            transaction.save(update_fields=["status", "payment_status", "updated_at"])
            logger.info("Stripe payment intent %s succeeded", transaction.transaction_id)

      elif event_type == 'payment_intent.payment_failed':
        logger.warning("Stripe reported a failed payment intent %s", event_id)
        payment_intent = event['data']['object']
        transaction = Transaction.objects.filter(transaction_id=payment_intent.get('id')).first()
        if transaction:
            transaction.status = payment_intent.get('status', 'failed')
            transaction.payment_status = 'failed'
            transaction.save(update_fields=["status", "payment_status", "updated_at"])
    except Exception as exc:
      StripeWebhookEvent.objects.filter(event_id=event_id).update(status="failed", last_error=str(exc)[:255])
      logger.exception("Stripe event processing failed event_id=%s", event_id)
      return HttpResponse(status=500)

    StripeWebhookEvent.objects.filter(event_id=event_id).update(status="processed", processed_at=timezone.now())

    return HttpResponse(status=200)
