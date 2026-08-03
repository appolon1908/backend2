import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("payment_app", "0002_stripewebhookevent"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="WebhookSubscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("url", models.URLField(max_length=1000)),
                ("name", models.CharField(max_length=120)),
                ("secret", models.CharField(max_length=255)),
                ("events", models.JSONField(default=list)),
                ("enabled", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="webhook_subscriptions", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="WebhookDelivery",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_id", models.UUIDField(default=uuid.uuid4, unique=True)),
                ("event_type", models.CharField(max_length=120)),
                ("payload", models.JSONField(default=dict)),
                ("status", models.CharField(choices=[("queued", "Queued"), ("delivered", "Delivered"), ("failed", "Failed"), ("retrying", "Retrying")], default="queued", max_length=16)),
                ("attempts", models.PositiveSmallIntegerField(default=0)),
                ("attempt_history", models.JSONField(default=list)),
                ("response_code", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("response_body", models.TextField(blank=True)),
                ("error", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("delivered_at", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("subscription", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="deliveries", to="payment_app.webhooksubscription")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
