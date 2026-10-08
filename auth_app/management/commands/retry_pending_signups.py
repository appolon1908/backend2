from django.core.management.base import BaseCommand, CommandError

from auth_app.models import User
from auth_app.tasks import queue_signup_sync
from helpers.middleware_client import MiddlewareConfigurationError, _config


class Command(BaseCommand):
    help = "Requeue a bounded batch of pending/failed signup intents; accepted operations are excluded."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        limit = options["limit"]
        if not 1 <= limit <= 1000:
            raise CommandError("--limit must be between 1 and 1000")
        try:
            _config()
        except MiddlewareConfigurationError:
            self.stdout.write("Integration not configured; no signup intents queued.")
            return
        user_ids = list(User.objects.filter(
            crm_sync_status__in=["pending", "failed"],
            crm_sync_operation_id="",
            odoo_id__isnull=True,
        ).exclude(crm_sync_payload={}).order_by("created_at").values_list("pk", flat=True)[:limit])
        queued = sum(queue_signup_sync(user_id) for user_id in user_ids)
        self.stdout.write(f"Queued {queued} of {len(user_ids)} pending signup intents.")
